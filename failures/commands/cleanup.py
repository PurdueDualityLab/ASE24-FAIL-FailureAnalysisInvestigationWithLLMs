import argparse
import logging
import textwrap
from django.db.models import Count

from failures.articles.models import Article, Incident

import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

class CleanUpCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the classify command

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure
        """

        parser.description = textwrap.dedent(
            """
            Clean up the database after each command.
            1. Reset incidents/incident relationships for non-failure articles
            2. Remove all incidents with 0 articles
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Clean up the database after each command.
            1. Remove all incidents with 0 articles

        Args: 
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser for the configuration
        """

        logging.info("\nCleaning up database.")

        # Init vector DB
        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal
        embedding_function = OpenAIEmbeddings()
        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)
        
        # Get list of articles that are not analyzable and have an incident tied to them
        articles = Article.objects.filter(describes_failure=False, incident__isnull=False)

        if articles:
            
            logging.info("Resetting incidents/incident relationships for non-failure articles")

            for article in articles:
                # Delete article from vectorDB
                logging.info("Deleting article " + str(article.id) + " from VectorDB")
                chunks_for_sampleArticle = vectorDB.get(where={"articleID": article.id})['ids']
                if chunks_for_sampleArticle:
                    vectorDB._collection.delete(ids=chunks_for_sampleArticle)

                # Set article incident to none, set article stored to false
                article.incident = None
                article.analyzable_failure = False
                article.article_stored = False
                article.save()

        # Get list of articles that are failures but not analyzable and have an incident tied to them
        articles = Article.objects.filter(describes_failure=True, analyzable_failure=False, incident__isnull=False)

        if articles:
            
            logging.info("Resetting incidents/incident relationships failure but not analyzable articles")

            for article in articles:
                # Delete article from vectorDB
                logging.info("Deleting article " + str(article.id) + " from VectorDB")
                chunks_for_sampleArticle = vectorDB.get(where={"articleID": article.id})['ids']
                if chunks_for_sampleArticle:
                    vectorDB._collection.delete(ids=chunks_for_sampleArticle)

                # Set article incident to none, set article stored to false
                article.incident = None
                article.article_stored = False
                article.save()

        # Get list of articles that are not failures and update accordingly
        articles = Article.objects.filter(describes_failure=False, analyzable_failure=True)

        for article in articles:
            article.analyzable_failure = False
            article.save()

        # Get list of incidents with 0 mapped articles
        incidents = Incident.objects.annotate(num_articles=Count('articles')).filter(num_articles=0)

        if incidents: 
            logging.info("Removing all incidents with 0 mapped articles.")

            for incident in incidents: 
                # Delete from vectorDB
                logging.info("Deleting incident " + str(incident.id) + " from Django and VectorDB.")
                chunks_for_incident = vectorDB.get(where={"incidentID": incident.id})['ids']
                if chunks_for_incident:
                    vectorDB._collection.delete(ids=chunks_for_incident)

                # Delete incident from Django
                incident.delete()

        logging.info("Database is clean!")
    
        