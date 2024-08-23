import argparse
import logging
import textwrap

import json
import math


from django.db.models import Q, Min

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import FAILURE_SYNONYMS, POSTMORTEM_QUESTIONS, TAXONOMY_QUESTIONS, TAXONOMY_DEFINITIONS, CPS_KEYS, PROMPT_ADDITIONS

import tiktoken

import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, DatetimeOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.output_parsers import DatetimeOutputParser
from langchain.output_parsers import OutputFixingParser


class PostmortemIncidentAutoVDBCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Create postmortems for SE failure incidents present in the database. If no arguments are provided, create postmortems for all
            SE failure incidents that do not have a postmortem; otherwise, if --all is provided, create postmortems for all
            SE failure incidents. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create postmortems for all incidents even if they already have a postmortem.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key. If all keys, set to 'all'.",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--incidents",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="Marks articles as part of the experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nCreating postmortems for incidents.")

        model_parameters = {"model": "gpt-3.5-turbo", "temperature": 0, "context_window": 16385}
        #model_parameters = {"model": "gpt-4-turbo-2024-04-09", "temperature": 0, "context_window": 128000} 

        query_all = args.all
        query_key = args.key
        # TODO: Key = all?

        # IF TESTING: Only fetching incidents related to article testing set
        if args.articles:
            incidents = Incident.objects.filter(articles__in=args.articles).distinct()
        elif args.incidents:
            incidents = Incident.objects.filter(id__in=args.incidents).distinct()
        elif query_all:
            incidents = Incident.objects.all()
        else:
            incidents = Incident.objects.filter(Q(new_article=True) | Q(complete_report=False) | Q(complete_report=None))


        # Order by ID
        incidents = incidents.order_by("id")
        
        # Exclude incidents where 'experiment' is True
        incidents = incidents.exclude(experiment=True)


        ### TODO: Temporary: order by published date in descending order
        # sorts the Incident objects in descending order based on their published dates. and prefetches all articles for each incident
        #incidents = Incident.objects.prefetch_related('articles').order_by('-published')[:200]        


        ### Importing prompts
        failure_synonyms = FAILURE_SYNONYMS

        postmortem_questions = POSTMORTEM_QUESTIONS.copy() 
        taxonomy_questions = TAXONOMY_QUESTIONS.copy()
        taxonomy_definitions = TAXONOMY_DEFINITIONS.copy()

        cps_keys = CPS_KEYS.copy()

        prompt_additions = PROMPT_ADDITIONS.copy()

        CHUNK_SIZE = 500

        ### Check if a specific question is to be queried
        if query_key != 'None' and query_key != "all":
            if query_key in postmortem_questions.keys():
                postmortem_questions = {}
                postmortem_questions[query_key] = POSTMORTEM_QUESTIONS[query_key]
            else: 
                postmortem_questions = {}
            
            if query_key in taxonomy_questions.keys():
                taxonomy_questions={}
                taxonomy_questions[query_key] = TAXONOMY_QUESTIONS[query_key]
            else:
                taxonomy_questions = {}
        
        ### ChatGPT
        chatGPT = ChatGPT()
        
        ### Set up for incidents > 16k context window
        # Vector DB setup
        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal
        embedding_function = OpenAIEmbeddings()
        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = CHUNK_SIZE, chunk_overlap = 0)

        prompt_window = model_parameters["context_window"] - 1500
        num_chunks = math.floor( prompt_window / CHUNK_SIZE ) #Number of chunks to retrieve 
        
        ### Set up for counting tokens in incident
        encoding = tiktoken.encoding_for_model(model_parameters["model"])


        ### System instructions for LLM to conduct failure analysis
        content = "You will help conduct failure analysis on software failure incidents reported by news articles."
        system_message = [
                {"role": "system", 
                "content": content}
                ]
        
        ## For open ended postmorterm questions & for Step 1 of taxonomy questions: To 'answer' information directly from articles
        prompt_template_articles_instruction = "Use the following news articles reporting on a software failure incident to answer the Question." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
                + "\n"+ "Cite the Article # for articles used to answer the question in the format: [#, #, ...]. If you can't answer the question using the articles, return 'unknown'." + "\n"
        
        ## For Step 1 of taxonomy questions: To 'extract' the information extracted from articles to answer questions
        prompt_template_extract_task = "Extract information from the articles about the software failure incident related to:\n"

        ## For Step 2 of taxonomy questions: To 'make decisions' using the extracted information about the taxonomy
        prompt_template_decision_instruction = "Use the following Extracted Information from news articles reporting on a software failure incident to answer the Questions." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
                + "\n"+ "If you can't answer the questions using the information, answer with 'unknown'." + "\n"
        prompt_template_decision_task = "Using the Extracted Information answer the following questions:\n"
        prompt_template_JSON_format = "\nReturn answers in the following JSON format:"


        successful_postmortem_creations = 0
        for incident in incidents:
            logging.info("Creating postmortem for incident %s.", incident.id)

            #If queryset is for an experiment mark it as such
            if args.experiment is True:
                incident.experiment = True

            ### Get related articles
            incident_articles = incident.articles.all()

            ### Count total number of tokens for all articles in an incident
            if incident.tokens == None or incident.new_article == True:  
                incident_tokens = 0

                for article in incident_articles:
                    if article.tokens == None:
                        article.tokens = len(encoding.encode(article.body))

                    incident_tokens += article.tokens
                
                incident.tokens = incident_tokens

            ### If incident token length is less than the model's context window, then directly prompt the model with the articles, if not then do RAG
            RAG_Pipeline = False
            if incident.tokens <= prompt_window: 
                RAG_Pipeline = False
                incident.rag = False
            else:
                logging.info("Using RAG for incident: " + str(incident.id))
                RAG_Pipeline = True
                incident.rag = True


            if RAG_Pipeline is False:
                # Add Articles for the Incident directly into a prompt template
                prompt_incident = ""
                for article in incident_articles:
                    prompt_incident += "\n" +"<Article " + str(article.id) + ">"
                    prompt_incident += article.body
                    prompt_incident += "</Article " + str(article.id) + ">" +"\n"
            
            
            if RAG_Pipeline is True:
                logging.info("Checking Vector DB for Incident: " + str(incident.id))

                ### Store articles in VectorDB
                for article in incident_articles:

                    ### Check if article is already stored:
                    if article.article_stored is not True:

                        article_body = article.body
                        articleID = article.id
                        incidentID = incident.id

                        updated_ids = self.store_articles(vectorDB, article_body, articleID, incidentID, text_splitter)
                                                
                        logging.info("Storing Article " + str(article.id) + " into Vector DB with IDs: " + str(vectorDB.get(updated_ids)))
                        
                        article.article_stored = True
                        article.save(update_fields=['article_stored'])
            

            ### Answer open ended postmortem questions
            for question_key in list(postmortem_questions.keys()): #[list(questions.keys())[i] for i in [0,1,2,10,11,12]]:
        
                # Check if the question has already been answered
                answer_set = True
                if not getattr(incident, question_key):
                    answer_set = False

                # Ask LLM
                if query_all or query_key == question_key or query_key == "all" or incident.new_article == True or answer_set == False or args.experiment is True: 
                    logging.info("Querying question: " + str(question_key))

                    ### Retrieve relevant chunks from articles for this incident from the VectorDB related to the Prompt
                    if RAG_Pipeline is True:

                        #TODO: Put this into a function so you can call it here as well as for the taxonomy

                        query = postmortem_questions[question_key]
                        incidentID = incident.id
                        
                        try:
                            dict_articles = self.retrieve_articles(vectorDB, query, incidentID, num_chunks)
                        except Exception as e:
                            logging.error(f"Error retrieving articles for this question, skipping question. Error: {e}")
                            continue

                        # Add Articles for the Incident into a prompt template
                        prompt_incident = ""
                        for articleID, articleBody in dict_articles.items():
                            prompt_incident += "\n" +"<Article " + str(articleID) + ">"
                            prompt_incident += articleBody
                            prompt_incident += "</Article " + str(articleID) + ">" +"\n"


                    ### Construct prompt
                    prompt_question = "\n<Question>" + prompt_additions[question_key]["before"] + postmortem_questions[question_key] + prompt_additions[question_key]["after"] + "</Question>"
                    #logging.info(prompt_question)
                    final_prompt = prompt_template_articles_instruction + prompt_incident + prompt_question

                    messages = system_message.copy()

                    messages.append(
                                    {"role": "user", "content": final_prompt},
                                    )
                    
                    model_parameters_temp = model_parameters.copy()
                    model_parameters_temp["messages"] = messages.copy()

                    #logging.info(type(model_parameters_temp))
                    #logging.info(model_parameters_temp)
            
                    reply = chatGPT.run(model_parameters_temp)
                    #logging.info("Reply:")
                    #logging.info(reply)

                    setattr(incident, question_key, reply)


            ### Answer choice-based taxonomy questions
            for question_key in list(taxonomy_questions.keys()): #[list(questions.keys())[i] for i in [0,1,2,10,11,12]]:

                # If question is for CPS, and the system for incident is not CPS, then don't answer
                if question_key in cps_keys and "TRUE" not in incident.cps_option: #incident.cps != True:
                        continue

                question_rationale_key = question_key + "_rationale"
                question_option_key = question_key + "_option"
            
                # Check if the question has already been answered
                answer_set = True
                if not getattr(incident, question_option_key):
                    answer_set = False

                # Ask LLM 
                if query_all or query_key == question_key or query_key == "all" or incident.new_article == True or answer_set == False or args.experiment is True: 
                    logging.info("Querying question: " + str(question_key))

                    ### Retrieve relevant chunks from articles for this incident from the VectorDB related to the Prompt
                    if RAG_Pipeline is True:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    

                        query = taxonomy_definitions[question_key]
                        incidentID = incident.id
                        
                        try:
                            dict_articles = self.retrieve_articles(vectorDB, query, incidentID, num_chunks)
                        except Exception as e:
                            logging.error(f"Error retrieving articles for this question, skipping question. Error: {e}")
                            continue

                        # Add Articles for the Incident into a prompt template
                        prompt_incident = ""
                        for articleID, articleBody in dict_articles.items():
                            prompt_incident += "\n" +"<Article " + str(articleID) + ">"
                            prompt_incident += articleBody
                            prompt_incident += "</Article " + str(articleID) + ">" +"\n"


                    ### Construct prompt to Ask LLM to extract relevent information from articles to help make the decision about the taxonomy
                    messages = system_message.copy()

                    prompt_question = "\n<Question>" + prompt_template_extract_task + prompt_additions[question_key]["rationale"]["before"] + taxonomy_definitions[question_key] + prompt_additions[question_key]["rationale"]["after"] + "</Question>"
                    
                    final_prompt = prompt_template_articles_instruction + prompt_incident + prompt_question

                    messages.append(
                                    {"role": "user", "content": final_prompt},
                                    )
                    
                    model_parameters_temp = model_parameters.copy()
                    model_parameters_temp["messages"] = messages.copy()

                    #logging.info(type(model_parameters_temp))
                    #logging.info(model_parameters_temp)

            
                    reply = chatGPT.run(model_parameters_temp)
                    #logging.info("Reply:")
                    logging.info(reply)


                    setattr(incident, question_rationale_key, reply)

                    #If invalid rationale, don't make decision
                    if reply is None:
                        continue

                    ### Construct prompt to Ask LLM to make the decision about the taxonomy using the extracted information
                    messages = system_message.copy()

                    extracted_info = "<Extracted Information>" + reply + "</Extracted Information>"
                    
                    prompt_question = "\n<Questions>" + prompt_template_decision_task + prompt_additions[question_key]["decision"]["before"] + taxonomy_questions[question_key] + prompt_template_JSON_format + prompt_additions[question_key]["decision"]["after"] + "</Questions>"

                    final_prompt = prompt_template_decision_instruction + extracted_info + prompt_question

                    messages.append(
                                    {"role": "user", "content": final_prompt},
                                    )
                    
                    model_parameters_temp = model_parameters.copy()
                    model_parameters_temp["messages"] = messages.copy()

                    model_parameters_temp["response_format"] = {"type": "json_object"}

                    #logging.info(type(model_parameters_temp))
                    #logging.info(model_parameters_temp)
            
                    reply = chatGPT.run(model_parameters_temp)
                    #logging.info("Reply:")
                    logging.info(reply)

                    ### Error handling for JSON format is implemented in ChatGPT class

                    ### Convert JSON to string with options that are true in csv format
                    if reply is not None:
                        reply = json.loads(reply)
                        if question_key == "cps" or question_key == "application":
                            if reply[question_key] is True:
                                reply = "TRUE"
                            elif reply[question_key] is False:
                                reply = "FALSE"
                            elif reply["unknown"] is True:
                                reply = "unknown"
                        else:
                            # Extract keys where the corresponding values are True
                            true_keys = [key for key, value in reply.items() if value]
                            # Convert the list of keys into a string
                            reply = ', '.join(true_keys)

                    setattr(incident, question_option_key, reply)

            
            # Query the related articles for the current incident and find the earliest published date
            if incident.published is None or incident.new_article is True:
                incident.published = incident.articles.aggregate(earliest_published=Min('published'))['earliest_published']


            ### Check if report is complete
            complete_report = True

            for question_key in list(POSTMORTEM_QUESTIONS.keys()):
                if not getattr(incident, question_key):
                    complete_report = False
                    break
            
            for question_key in list(TAXONOMY_QUESTIONS.keys()):
                
                # If question is for CPS, and the system for incident is not CPS, then don't check for its completion
                if question_key in cps_keys and "TRUE" not in incident.cps_option: #incident.cps != True:  ###"\"cps\": true"
                    continue

                question_option_key = question_key + "_option"
                if not getattr(incident, question_option_key) or complete_report == False:
                    complete_report = False
                    break
            
            if complete_report == True:
                incident.complete_report = True
            else:
                incident.complete_report = False

            ### All new articles for the incidents would have contributed to the incident
            incident.new_article = False
            
            
            incident.save()

            logging.info("Succesfully created postmortem for incident %s: %s.", incident.id, incident.title)
            successful_postmortem_creations += 1
            

        logging.info("Successfully created postmortems for %d incidents.", successful_postmortem_creations)

    def store_articles(self, vectorDB, article_body, articleID, incidentID, text_splitter):
        """
        Store article chunks into vectorDB. 
        """

        metadata = [{"incidentID": incidentID, "articleID": articleID}]

        document = text_splitter.create_documents([article_body], metadatas=metadata)
        
        document_splits = text_splitter.split_documents(document)

        for order, document in enumerate(document_splits): # To keep track of the order of the chunks
            document.metadata["order"] = order
        
        updated_ids = vectorDB.add_documents(document_splits)

        return updated_ids
    
    
    def retrieve_articles(self, vectorDB, query, incidentID, num_chunks):
        """
        Retrieve article chunks from vectorDB. 
        """

        ##Get as many chunks as possible relevant to the query from the VectorDB from all articles from the incident
        docs = vectorDB.similarity_search(query=query, filter={"incidentID":incidentID}, k = num_chunks)

        ##Convert these chunks into condensed articles 
        dict_docs = {}
        for doc in docs:
            articleID = doc.metadata["articleID"]
            order = doc.metadata["order"]
            page_content = doc.page_content
            
            if articleID in dict_docs:
                dict_docs[articleID].append((order, page_content))
            else:
                dict_docs[articleID] = [(order, page_content)]
        
        #Sort the page_content for each articleID based on order
        for articleID in dict_docs:
            sorted_page_contents = [content for _, content in sorted(dict_docs[articleID])]
            dict_docs[articleID] = ' '.join(sorted_page_contents) 

        # Sort dict_docs by articleID in ascending order
        dict_docs = dict(sorted(dict_docs.items()))

        return dict_docs
