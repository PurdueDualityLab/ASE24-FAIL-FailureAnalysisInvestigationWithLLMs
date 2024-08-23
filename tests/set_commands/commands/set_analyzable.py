import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, Incident

class SetAnalyzableCommand:
    INPUT_FILE_PATH = "tests/set_commands/manual_states/desired_state.csv"

    def __init__(self):
        pass

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the save set analyzable_failure command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Set the article's analyzable_failure flag to the input csv's value.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the set analyzable_failure state command.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Define the columns to read
        columns_to_read = ["article_id", "analyzable_failure"]

        # Read the Excel file into a Pandas DataFrame
        file_path = self.INPUT_FILE_PATH
        try:
            df = pd.read_csv(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return 

        
        # Iterate over each row in the DataFrame
        for index, row in df.iterrows():
            article_id = row["article_id"]
            analyzable_failure_csv = row["analyzable_failure"]

            if type(analyzable_failure_csv) == bool:
                analyzable_failure = analyzable_failure_csv
            else:
                analyzable_failure = False

            # Fetch the Article object from the database
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                logging.warning(f"Article with ID {article_id} does not exist.")
                continue

            # Update the analyzable_failure attribute
            article.analyzable_failure = analyzable_failure
            article.save()

        logging.info("analyzable_failure attributes updated successfully.")

        return
