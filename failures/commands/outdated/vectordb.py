import os
import argparse
import logging
import textwrap

from django.db.models import Q
from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT,  ClassifierChatGPT
from failures.parameters.models import Parameter

import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectordbCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Vectorize and store article bodies into vector database. If no arguments are provided, 
            only new articles and incidents will be vectorized and stored; otherwise, 
            if --all is provided, all articles will be re-vectorized and re-stored into the database. 
            If --articles is provided, only the articles given in the list will be vectorized
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Redo vectorization and storage for all incidents.",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        
        logging.info("\nUpdating Vector Database.")
        
        '''
        if args.all:
            incidents = Incident.objects.all()
        else:
            incidents = (
                    Incident.objects.filter(
                        Q(incident_updated=True) | ~Q(incident_stored=True)
                    )
                    )
        '''
        incidents = Incident.objects.all()

        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal

        if args.all and not args.articles:
            chroma_client.reset()
            #TODO: rather than reset, dissaciate the chunks' metadata for incident ID. And in the for loop, if article id is already in VectorDB then just add incident ID
        
        embedding_function = OpenAIEmbeddings()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)

        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)

        # chunks_for_sampleArticle = vectorDB.get(where={"articleID": 116})
        # print(chunks_for_sampleArticle)
        # vectorDB._collection.delete(where={"articleID": 116})

        # Remove any article in args.articles from the vector database
        if args.articles:
            logging.info("Deleting all articles in args.articles from the vector database.")
        for articleID in args.articles:
            logging.info("Removing article ID: " + str(articleID) + " from vectorDB")
            chunks_for_sampleArticle = vectorDB.get(where={"articleID": articleID})['ids']
            if chunks_for_sampleArticle:
                vectorDB._collection.delete(ids=chunks_for_sampleArticle)
 
        count1 = 0
        count2 = 0
        # Iterate through incidents
        for incident in incidents:

            logging.info("Incident ID: "+ str(incident.id))
            
            # Get related articles for the current incident
            if args.articles:
                articles = Article.objects.filter(incident=incident, id__in=args.articles) # Collects only articles that are related to testing suite
            elif args.all:
                articles = Article.objects.filter(incident=incident)
            else:
                articles = Article.objects.filter( Q(incident=incident,article_stored=False) | Q(incident=incident,article_stored__isnull=True) )
            
            # Iterate through articles for the current incident
            for article in articles:
                logging.info("Article ID: "+ str(article.id))

                metadata = [{"incidentID": incident.id, "articleID": article.id}]

                document = text_splitter.create_documents([article.body], metadatas=metadata)
                
                document_splits = text_splitter.split_documents(document)
                
                updated_ids = vectorDB.add_documents(document_splits)

                #updated_ids = vectorDB.add_texts(texts=[article.body], metadatas=metadata, ids=[str(article.id)]) #For storing without chunking
                
                #logging.info("Stored: " + str(vectorDB.get(updated_ids)) + " in VectorDB")
                
                article.article_stored = True
                article.save()
                
            
            
        
        #logging.info("Stored: " + str(vectorDB.get(updated_ids)) + " in VectorDB")
        logging.info("Articles vectorized!")
