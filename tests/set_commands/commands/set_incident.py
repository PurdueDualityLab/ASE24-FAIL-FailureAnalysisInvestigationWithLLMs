import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, Incident
from failures.commands.PROMPTS import QUESTIONS
from failures.networks.models import ChatGPT, EmbedderGPT,  ClassifierChatGPT

class SetIncidentCommand:
    INPUT_FILE_PATH = "tests/set_commands/manual_states/manual_merge.csv"
    OUTPUT_FILE_PATH = "tests/set_commands/saved_states/manual_to_db_incident_map.csv"

    def __init__(self):
        pass

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the set incident command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Set the article's incident to the desired state.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the set incident state command.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        logging.info("Updating article's incident attributes.")

        logging.info("Clearing all experimental flags from incidents.")
        
        # Getting all current experimental incidents
        incidents = Incident.objects.filter(experiment=True)

        # Setting all incident experiment flags to false
        for incident in incidents:
            incident.experiment = False
            incident.save()

        # Define the columns to read
        columns_to_read = ["article_id", "incident"]

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
        
        # Filter out rows where incident is null
        df = df[df["incident"].notnull()]

        # Convert incident column to Python integers
        df["incident"] = df["incident"].apply(lambda x: int(x))

        # Initialize an empty dictionary to store article IDs for each incident
        incident_dict = {}

        # Iterate over each row in the DataFrame
        for index, row in df.iterrows():
            article_id = row["article_id"]
            incident = row["incident"]

            # Skip rows with NaN incidents
            if pd.isnull(incident):
                continue

            # Convert to int
            incident = int(incident)

            # If incident not in dictionary, add it with empty list
            if incident not in incident_dict:
                incident_dict[incident] = []

            # Append article ID to the corresponding incident key
            incident_dict[incident].append(int(article_id))

        # Set up merge
        inputs = {"model": "gpt-3.5-turbo", "temperature": 0}
        logging.info("\nUsing " + inputs["model"] + " with a temperature of " + str(inputs["temperature"]) + ".")

        questions = {key: QUESTIONS[key] for key in ["title", "summary"]}

        questions_chat = questions

        postmortem_keys = ["summary"]
        weights = [1]

        chatGPT = ChatGPT()
        embedder = EmbedderGPT()

        # Create incident map from manual value to db value
        manual_to_db_map = []

        # Changing mappings
        for incident in incident_dict.keys():

            # Get list of articles for incident and query
            article_ids = incident_dict[incident]
            articles = Article.objects.filter(id__in=article_ids)

            if not articles:
                continue

            # Take first article and create title
            start_article = articles[0]
            start_article.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, False, "title") # TODO: Look into if 'query_all' should be True or False

            logging.info("Creating new incident: %s.", start_article.title)

            # Create new incident
            new_incident = Incident.objects.create(title=start_article.title, published=start_article.published, experiment=True)

            # Add to map
            manual_to_db_map.append((incident, new_incident.id))

            # Add articles to incident
            for article in articles:

                # Create embeddings for the new article's postmortem information
                article.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, False, "summary")

                article.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

                # Set incident
                article.incident = new_incident

                article.save()

        logging.info("Article's incident attributes done updating.")

        logging.info("Saving manual incident id to db incident id mapping to " + self.OUTPUT_FILE_PATH + ".")

        with open(self.OUTPUT_FILE_PATH, mode='w', newline='') as csv_file:
            fieldnames = ["Manual", "DB"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Writing the header
            writer.writeheader()

            temp_map = {
                "Manual": 0,
                "DB": 0
            }

            # Writing the ids
            for mapping in manual_to_db_map:
                temp_map["Manual"] = mapping[0]
                temp_map["DB"] = mapping[1]
                writer.writerow(temp_map)

        logging.info("Validating results")

        for mapping in manual_to_db_map:
            manual_articles = set(incident_dict[mapping[0]])

            incident_id = mapping[1]

            try:
                # Get the Incident object using the ID
                incident = Incident.objects.get(pk=incident_id)

                # Use related manager to access associated articles
                articles = incident.articles.all()

                # Extract a list of article IDs
                db_articles = set(article.id for article in articles)
            except Incident.DoesNotExist:
                logging.warning(f"Incident with ID {incident_id} not found. Returning empty list.")
                continue

            if not (db_articles == manual_articles):
                logging.warning(f"Manual articles do not match db articles for manual incident {mapping[0]}. \nManual: {str(manual_articles)}\nDB: {str(db_articles)}")

        return
