import argparse
import logging
import textwrap
import time

from failures.articles.models import Article
from failures.networks.models import ZeroShotClassifier, ClassifierChatGPT
from failures.parameters.models import Parameter

import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

class ClassifyAnalyzableCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the classify command

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure
        """

        parser.description = textwrap.dedent(
            """
            Classify the articles reporting on softwar failures as whether they contain enough information for failure analysis. 
            If no arguments are provided, classify all articles that do not have a classification; otherwise, if --all is provided,
            classify all articles. If an article does not have a body, it will not be classified. 
            --sample is used for testing.
            --temp sets the ChatGPT temperature
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Classify all articles even if they already have a classification.",
        )
        parser.add_argument(
            "--sample",
            type=int,
            help="Dictates the number of samples",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--temp",
            type=float,
            default=0,
            help="Sets the temperature for ChatGPT",
        )
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="Marks articles as part of the experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article classification process based on provided arguments.

        Args: 
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser for the configuration
        """
        logging.info("\nClassifying articles on whether they contain information for software failure analysis.")

        # Gets list of article to classify
        queryset = (
            Article.objects.filter(describes_failure=True, id__in=args.articles) if args.articles else
            Article.objects.filter(describes_failure=True) if args.all else
            Article.objects.filter(describes_failure=True, analyzable_failure=None)
        )
        
        ### If queryset is for an experiment mark it as such
        if args.experiment is True:
            queryset.update(experiment=True)
        
        # Initializes ChatGPT Classifier
        classifierChatGPT = ClassifierChatGPT()

        # Handles inputs and temperature
        if 0 <= args.temp <= 1:
            temperature = args.temp
        else:
            logging.info("\nTemperature out of range [0,1]. Please check input.")
            exit()
        
        inputs = {"model": "gpt-3.5-turbo", "temperature": temperature} #gpt-3.5-turbo , gpt-4-1106-preview
        logging.info("\nUsing " + inputs["model"] + " with a temperature of " + str(temperature) + ".")
        
        analyzable_positive_classifications_ChatGPT = 0

        for article in queryset:
            
            logging.info("Classifying %s.", article)

            if article.classify_as_analyzable_ChatGPT(classifierChatGPT, inputs):
                analyzable_positive_classifications_ChatGPT += 1
                logging.info("ChatGPT Classifier: Classification met as eligible for failure analysis for article: " + str(article))


        logging.info("ChatGPT successfully classified %d articles as eligible for failure analysis.", analyzable_positive_classifications_ChatGPT)

        self.process_incident()

        

    def process_incident(self):
        """
        Remove incidents/incident relationships for articles not analyzable for postmortem.
        Also remove article and incident (if no other articles in incident) from vectorDB. 

        Args:
        """
        
        # Get list of articles that are not analyzable and do not have an incident tied to them
        articles = Article.objects.filter(analyzable_failure=False, incident__isnull=False)

        if articles:

            logging.info("Cleaning up database")

            logging.info("Resetting incidents/incident relationships for analyzable articles")

            # Init vector DB
            chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal
            embedding_function = OpenAIEmbeddings()
            vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)

            for article in articles:

                # Get associated incident
                incident = article.incident

                # Check if there is only one article associated with the incident
                if incident.articles.count() == 1 and incident.articles.first() == article:
                    # Delete from vectorDB
                    logging.info("Deleting incident " + str(incident.id) + " from Django and VectorDB.")
                    chunks_for_incident = vectorDB.get(where={"incidentID": incident.id})['ids']
                    if chunks_for_incident:
                        vectorDB._collection.delete(ids=chunks_for_incident)

                    # Delete incident from Django
                    incident.delete()

                # Delete article from vectorDB
                logging.info("Deleting article " + str(article.id) + " from incident " + str(article.incident.id) + " from VectorDB")
                chunks_for_sampleArticle = vectorDB.get(where={"articleID": article.id})['ids']
                if chunks_for_sampleArticle:
                    vectorDB._collection.delete(ids=chunks_for_sampleArticle)

                # Set article incident to none, set article stored to false
                article.incident = None
                article.article_stored = False
                article.save()



