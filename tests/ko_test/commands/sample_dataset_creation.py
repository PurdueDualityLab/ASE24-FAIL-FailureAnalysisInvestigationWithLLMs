import argparse
import logging
import textwrap
import pandas as pd
import csv
import random

from failures.articles.models import Article_Ko, SearchQuery, Incident_Ko
from datetime import datetime
from django.utils import timezone


class SampleDatasetCreationCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the generate article ids command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Generates a random list of articles from the Ko manual database. 30 describing failure according to our classification
            and 30 not describing failures. 


            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Generates random list of article IDs given parameters and stores to to CSV files. 

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Set random see
        random.seed(5)

        # Load in manual dataset containing mapping between non-failure and failure
        consensus_csv_path = "tests/ko_test/data/Ko_Stories_Consensus.csv"
        df = pd.read_csv(consensus_csv_path)

        # Get all incidents
        articles = Article_Ko.objects.all()

        # Get 30 non-failure incidents
        non_failure_articles = list(articles.filter(describes_failure=False).order_by('?')[:30])

        # Get 30 failure incidents
        failure_articles = list(articles.filter(describes_failure=True).order_by('?')[:30])

        # Randomly merge all the articles into one list
        all_manual_articles = non_failure_articles + failure_articles
        random.shuffle(all_manual_articles)

        print(len(all_manual_articles))

        # Create a list of DataFrames to store the data
        dfs = []

        # Iterate through all_manual_articles and append DataFrames to the list
        for article in all_manual_articles:
            dfs.append(pd.DataFrame({
                'storyID': str(int(df[df['DjangoArticleID'] == article.id]['storyID'].values[0])),
                'articleID': str(int(df[df['DjangoArticleID'] == article.id]['articleID'].values[0])),
                'rater': None  # You can fill out the rater value as needed
            }, index=[0]))

        # Concatenate all DataFrames into one
        output_df = pd.concat(dfs, ignore_index=True)

        # Optionally, save the DataFrame to a CSV file
        output_csv_path = "tests/ko_test/data/manual/manual_ko.csv"
        output_df.to_csv(output_csv_path, index=False)

        # Create a list of DataFrames to store the data for the automated answers
        dfs = []

        # Iterate through all_manual_articles and append DataFrames to the list
        for article in all_manual_articles:
            dfs.append(pd.DataFrame({
                'storyID': str(int(df[df['DjangoArticleID'] == article.id]['storyID'].values[0])),
                'articleID': str(int(df[df['DjangoArticleID'] == article.id]['articleID'].values[0])),
                'Django Classification': str(article.describes_failure)  # You can fill out the rater value as needed
            }, index=[0]))

        # Concatenate all DataFrames into one
        output_df = pd.concat(dfs, ignore_index=True)

        # Optionally, save the DataFrame to a CSV file
        output_csv_path = "tests/ko_test/data/auto/auto_ko.csv"
        output_df.to_csv(output_csv_path, index=False)

        return 0

   