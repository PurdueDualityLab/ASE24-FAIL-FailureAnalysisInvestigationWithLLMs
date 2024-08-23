import argparse
import logging
import textwrap
import pandas as pd
from openpyxl import load_workbook
from django.core import serializers
import random
import os
import csv

from failures.articles.models import Article, SearchQuery
from failures.commands.classifyAnalyzable import ClassifyAnalyzableCommand #TODO: Update the rest of the code with this
from failures.commands.classifyFailure import ClassifyFailureCommand #TODO: Update the rest of the code with this
from failures.commands.merge import MergeCommand
from failures.commands.vectordb import VectordbCommand

from failures.commands.postmortemIncidentAutoVDB import PostmortemIncidentAutoVDBCommand

from failures.commands.cluster import ClusterCommand
from tests.commands.evaluate_classification import EvaluateClassificationCommand
from tests.commands.evaluate_identification import EvaluateIdentificationCommand
from tests.commands.evaluate_merge import EvaluateMergeCommand

import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

class EvaluateTemperatureCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate different temperatures.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM using different temperatures. If no arguments are provided then 
            sample set of size 20 is going to be taken from the database and tested at different temperatures. 
            If --all is provided then all of the articles in the database are going to be used. 
            --sample = (int) can be used to set the number of samples taken to test with.
            --articles = [(ints)] can be used to determine which articles are sampled (this will override --sample).
            """
        )
        # Need to implement
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
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
            "--list",
            action="store_true",
            help="List all articles incorrectly classified.",
        )
        parser.add_argument(
            "--noEval",
            action="store_true",
            help="Does not evaluate commands, just runs them.",
        )
        parser.add_argument(
            "--noRun",
            action="store_true",
            help="Does not run the commands, just evaluates.",
        )
        parser.add_argument(
            "--startClassifyFailure",
            action="store_true",
            help="Starts testing the pipeline at classify (Defualt).",
        )
        parser.add_argument(
            "--startClassifyAnalyze",
            action="store_true",
            help="Starts testing the pipeline at classify (Defualt).",
        )
        parser.add_argument(
            "--startMerge",
            action="store_true",
            help="Starts testing the pipeline at merge.",
        )
        parser.add_argument(
            "--startVectorDB",
            action="store_true",
            help="Starts testing the pipeline at vectorDB.",
        )
        parser.add_argument(
            "--startPostmortemInicdent",
            action="store_true",
            help="Starts testing the pipeline at postmortemIncident.",
        )
        parser.add_argument(
            "--startCluster",
            action="store_true",
            help="Starts testing the pipeline at cluster.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key for all articles.",
        )
        parser.add_argument(
            "--end",
            type=int,
            help="Dictates the number of samples",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """

        logging.info("\n\nStarting experiment pipeline.")

        # Define the file path
        file_path = "./tests/manual_evaluation/perfect_merge.xlsx"

        # Define the columns to read
        columns_to_read = ["id"]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_excel(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return

        # Filter rows where 'id' is not a positive integer and 'Describes Failure?' is not 0 or 1
        article_ids = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]['id'].tolist()

        # Get number of samples
        if not args.articles:
            num_sample = args.sample if args.sample else 20
            num_sample = min(len(article_ids), num_sample)
        else:
            num_sample = len(args.articles)
        
        # Get 20 random articles if articles not explicitly defined
        if not args.articles:
            article_ids = random.sample(list(article_ids), num_sample)
            args.articles = article_ids

        # Set temperatures
        if 0.0 <= args.temp <= 1.0:
            temperatures = [args.temp]
            logging.info("Evaluation pipeline for temperature: " + str(args.temp))
        else:
            temperatures = [0.1 * x for x in range(0, 11)]

        # Create Dataframe to store evaluation
        # column_names = list(['Temperature','Accuracy (Percentage)', 'Sample Size', 'Accuracy (Fraction)', 'False Positive (Percentage)', 'False Positive (Fraction)', 'False Negative (Percentage)', 'False Negative (Fraction)', 'Wrong (Percentage)', 'Wrong (Fraction)', 'Total Evaluated'])
        # df = pd.DataFrame(columns=column_names)
        dfs = []

        # Get starting point for testing
        start = 0
        if args.startClassifyFailure:
            start = 0 # Redundant
        elif args.startClassifyAnalyze:
            start = 1
        elif args.startMerge:
            start = 2
        elif args.startVectorDB:
            start = 3
        elif args.startPostmortemInicdent:
            start = 4
        elif args.startCluster:
            start = 5

        # Get ending point for testing
        if not args.end:
            end = 10
        else:
            end = args.end

        logging.info("Temperatures: " + str(temperatures))
        for temperature in temperatures:
            args.temp = temperature

            # Blank metrics
            all_metrics = {}
            classification_metrics = {}
            identification_metrics = {}
            merge_metrics = {}

            # CLASSIFICATION & EVALUATION
            if start <= 0 and end >= 0:
                if not args.noRun:
                    logging.info("Classifying articles on whether report on software failures with a " + str(temperature) + " temperature.")
                    # run command
                    classifyFailure = ClassifyFailureCommand()
                    classifyFailure.run(args, parser)

                if not args.noEval:
                    # classify
                    evaluate_classify = EvaluateClassificationCommand()
                    classification_metrics = evaluate_classify.run(args, parser)

            if start <= 1 and end >= 1:
                if not args.noRun:
                    logging.info("Classifying articles on whether they contain information for software failure analysis with a " + str(temperature) + " temperature.")
                    # run command
                    ClassifyAnalyzable = ClassifyAnalyzableCommand()
                    ClassifyAnalyzable.run(args, parser)

                if not args.noEval:
                    # Identify
                    evaluate_identify = EvaluateIdentificationCommand()
                    identification_metrics = evaluate_identify.run(args, parser)

            # MERGING & EVALUATION
            if start <= 2 and end >= 2:
                if not args.noRun:
                    logging.info("Merging articles with a " + str(temperature) + " temperature.")
                    # run command
                    merge = MergeCommand()
                    merge.run(args, parser)

                if not args.noEval:
                    # merge
                    evaluate_merge = EvaluateMergeCommand()
                    merge_metrics = evaluate_merge.run(args, parser)

            # VECTORDB & EVALUATION
            if start <= 3 and end >= 3:
                if not args.noRun:
                    logging.info("Vectorizing articles.")
                    # run command
                    args.all = False
                    vectorDB = VectordbCommand()
                    vectorDB.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # vector
                    pass

            # POSTMORTEM INCIDENT & EVALUATION
            if start <= 4 and end >= 4:
                if not args.noRun:
                    logging.info("Analyzing postmortem with a " + str(temperature) + " temperature.")
                    args.all = True
                    # postmortem = PostmortemIncidentCommand()
                    # postmortem.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # postmortem incident
                    pass

            # CLUSTER & EVALUATION
            if start <= 5 and end >= 5:
                if not args.noRun:
                    logging.info("Clustering incidents with a " + str(temperature) + " temperature.")
                    cluster = ClusterCommand()
                    cluster.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # cluster
                    pass

            # Adding addtional metrics then appending excel sheet
            all_metrics["Temperature"] = str(args.temp)
            all_metrics["Sample Size"] = str(num_sample)
            if classification_metrics:
                all_articles.update(classification_metrics)
            if identification_metrics:
                all_metrics.update(identification_metrics)
            if merge_metrics:
                all_metrics.update(merge_metrics)

            # Convert to dataframe
            df_temp = pd.DataFrame([all_metrics])
            dfs.append(df_temp)

            # Get all information about articles recently classified and store in dataframe
            articles = Article.objects.filter(id__in=args.articles)
            serialized_data = serializers.serialize('python', articles)
            article_data_list = []

            for entry in serialized_data:
                article_data = entry['fields']
                article_data['Article ID'] = entry['pk']
                article_data_list.append(article_data)

            article_df = pd.DataFrame(article_data_list)

            # Create dataframe and store in CSV
            csv_path = f'./tests/performance/temperature{temperature:.1f}.csv'
            article_df.to_csv(csv_path, index=False)
            logging.info("Wrote to " + csv_path)

        # Convert dataframe to CSV
        df = pd.concat(dfs, ignore_index=True)
        csv_path = './tests/performance/temperature.csv'
        df.to_csv(csv_path, index=False)

    def process_incident(self, article_ids):
        """
        Remove incidents/incident relationships for articles not analyzable for postmortem.
        Also remove article and incident (if no other articles in incident) from vectorDB. 

        Args:
            article_ids (list): List of article ids to check
        """
        logging.info("Resetting incidents/incident relationships for analyzable articles")

        if not article_ids:
            logging.info("Articles not defined")
            return
        
        # Get list of articles that are not analyzable and do not have an incident tied to them
        articles = Article.objects.filter(id__in=article_ids, analyzable_failure=False, incident__isnull=False)

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
            logging.info("Deleting article " + str(article.id) + " from VectorDB")
            chunks_for_sampleArticle = vectorDB.get(where={"articleID": article.id})['ids']
            if chunks_for_sampleArticle:
                vectorDB._collection.delete(ids=chunks_for_sampleArticle)

            # Set article incident to none, set article stored to false
            article.incident = None
            article.article_stored = False
            article.save()