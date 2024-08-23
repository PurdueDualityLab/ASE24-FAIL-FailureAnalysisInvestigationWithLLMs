import argparse
import logging
import textwrap
import pandas as pd
from datetime import datetime
import os

from failures.articles.models import Article_Ko


class ScrapeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the scrape command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Scrape articles from Google News RSS feeds. If no arguments are provided, use all search
            queries present in the database; otherwise, use the provided arguments to create a new search query.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article scraping process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # # Retrieve and delete all articles from the database (preventing duplicates)
        all_articles = Article_Ko.objects.all()

        # for article in all_articles:
        #     print(article)
        # return
        all_articles.delete()

        # return

        logging.info("\nScraping articles_ko")

        # Consensus folder
        consensus_csv_path = "tests/ko_test/data/Ko_Stories_Consensus.csv"

        # Read consensus CSV file
        df = pd.read_csv(consensus_csv_path)

        # Story folder
        main_folder = "tests/ko_test/data/stories"

        # Set to store unique story IDs without 'invalid' consensus
        unique_story_ids = set()

        # Iterate through each story folder
        for story_folder in os.listdir(main_folder):
            story_folder_path = os.path.join(main_folder, story_folder)
            
            # Check if folder is a folder
            if not os.path.isdir(story_folder_path):
                continue

            # Check if the story has a consensus other than 'invalid'
            if 'invalid' not in df[df['storyID'] == int(story_folder)]['Consensus'].values:
                unique_story_ids.add(int(story_folder))

            # Iterate through articles in story
            for article_file in os.listdir(story_folder_path):
                article_file_path = os.path.join(story_folder_path, article_file)

                # Check if its a file
                if not os.path.isfile(article_file_path):
                    continue

                article_id = int(article_file.split('.')[0])

                # Read the first 4 lines into variables
                with open(article_file_path, 'r') as article_file:
                    headline = article_file.readline().strip()
                    published_date = article_file.readline().strip()
                    source = article_file.readline().strip()
                    db = article_file.readline().strip()

                    # Read the rest of the file into the body variable
                    body = article_file.read()

                    # Converted date time
                    converted_published_date = datetime.strptime(published_date, "%m/%d/%Y")

                    # Create a new Article_Ko object
                    new_article = Article_Ko(
                        headline=headline,
                        published=converted_published_date,
                        source=source,
                        body=body
                    )

                    # Set the relevant_to_story field based on consensus value
                    consensus_value = df[(df['storyID'] == int(story_folder)) & (df['articleID'] == article_id)]['Consensus'].values[0]

                    if consensus_value == 'invalid':
                        print("This is a problem, invalid consensus made it to django")

                    new_article.relevant_to_story = consensus_value == 'relevant'

                    new_article.save()

                    # Update the 'article_id' in the DataFrame with the correct article ID
                    df.loc[(df['storyID'] == int(story_folder)) & (df['articleID'] == article_id), 'DjangoArticleID'] = new_article.id

        # Write updated csv back
        df.to_csv(consensus_csv_path, index=False)

        # Log logistics
        total_articles = Article_Ko.objects.count()
        relevant_articles = df[df['Consensus'] == 'relevant'].shape[0]
        offtopic_articles = df[df['Consensus'] == 'offtopic'].shape[0]
        unique_story_ids_count = len(unique_story_ids)

        logging.info(f"\nTotal Articles in Database: {total_articles}")
        logging.info(f"Number of Relevant Articles: {relevant_articles}")
        logging.info(f"Number of Off-topic Articles: {offtopic_articles}")
        logging.info(f"Number of Unique Story IDs without 'invalid' consensus: {unique_story_ids_count}")


        