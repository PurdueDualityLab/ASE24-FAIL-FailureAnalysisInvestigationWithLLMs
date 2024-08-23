import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, Incident

class SaveStateCommand:
    INPUT_FILE_PATH = "tests/set_commands/manual_states/article_ids.csv"
    OUTPUT_FILE_PATH = "tests/set_commands/saved_states/"

    def __init__(self):
        pass

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the save state command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Save the state of all of the articles and associated incidents for the manual analysis.
            """
        )
        parser.add_argument(
            "--stateNum",
            type=int,
            help="The state number to save the articles/incidents",
            required=True,
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the save state command.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Define the columns to read
        columns_to_read = ["article_id"]

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

        # Get ids list
        ids = df['article_id'].tolist()

        # Download articles
        article_file_path = self.OUTPUT_FILE_PATH + "article_state" + str(args.stateNum) + ".csv"
        articles = Article.objects.filter(id__in=ids)
        self.download_article_data_to_csv(articles, file_path=article_file_path)

        # Download incidents
        incident_file_path = self.OUTPUT_FILE_PATH + "incident_state" + str(args.stateNum) + ".csv"
        incidents = Incident.objects.filter(articles__id__in=ids)
        self.download_incident_data_to_csv(incidents, file_path=incident_file_path)

        logging.info(f"Saved current state. (state id={str(args.stateNum)})")
        return

    def download_article_data_to_csv(self, article_ids: list, file_path: str = 'tests/set_commands/saved_states/incident_state_0.csv') -> None:
        """
        Downloads article data to a CSV file.

        Args:
            article_ids (list): List of article IDs to download.
            file_path (str): Path to the CSV file. Defaults to 'tests/fetched_data/article_data.csv'.

        Returns:
            None
        """
        try:
            logging.info("Downloading article data to CSV.")

            # Fetch articles based on provided article ids
            articles = Article.objects.filter(id__in=article_ids)

            # Define CSV header with article ID and related incident IDs
            header = ["Article ID", "Related Incident IDs"] + [
                "Published", "URL", "Source", "Article Summary", "Body", "Scraped At",
                "Scrape Successful", "Describes Failure", "Analyzable Failure", "Article Stored",
                "Similarity Score", "Headline", "Title", "Summary", "System", "Time", "SEcauses",
                "NSEcauses", "Impacts", "Preventions", "Fixes", "ResponsibleOrg", "ImpactedOrg",
                "References", "Phase Option", "Boundary Option", "Nature Option", "Dimension Option",
                "Objective Option", "Intent Option", "Capability Option", "Duration Option",
                "Domain Option", "CPS Option", "Perception Option", "Communication Option",
                "Application Option", "Behaviour Option", "Phase Rationale", "Boundary Rationale",
                "Nature Rationale", "Dimension Rationale", "Objective Rationale", "Intent Rationale",
                "Capability Rationale", "Duration Rationale", "Domain Rationale", "CPS Rationale",
                "Perception Rationale", "Communication Rationale", "Application Rationale",
                "Behaviour Rationale"
            ]

            # Open CSV file and write header
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(header)

                # Write article data
                for article in articles:
                    # Fetch related incident IDs
                    related_incident_ids = related_incident_ids = [article.incident.id] if article.incident else []

                    # Write row with article ID and related incident IDs
                    csv_writer.writerow([article.id, related_incident_ids] + [
                        article.published, article.url, article.source, article.article_summary,
                        article.body, article.scraped_at, article.scrape_successful, article.describes_failure,
                        article.analyzable_failure, article.article_stored, article.similarity_score,
                        article.headline, article.title, article.summary, article.system, article.time,
                        article.SEcauses, article.NSEcauses, article.impacts, article.preventions,
                        article.fixes, article.ResponsibleOrg, article.ImpactedOrg, article.references,
                        article.phase_option, article.boundary_option, article.nature_option,
                        article.dimension_option, article.objective_option, article.intent_option,
                        article.capability_option, article.duration_option, article.domain_option,
                        article.cps_option, article.perception_option, article.communication_option,
                        article.application_option, article.behaviour_option, article.phase_rationale,
                        article.boundary_rationale, article.nature_rationale, article.dimension_rationale,
                        article.objective_rationale, article.intent_rationale, article.capability_rationale,
                        article.duration_rationale, article.domain_rationale, article.cps_rationale,
                        article.perception_rationale, article.communication_rationale, article.application_rationale,
                        article.behaviour_rationale
                    ])

            logging.info(f"Article data downloaded to CSV: {file_path}")

        except Exception as e:
            logging.error(f"Error downloading article data to CSV: {str(e)}")

    def download_incident_data_to_csv(self, incident_ids: list, file_path: str = 'tests/set_commands/saved_states/article_state_0.csv') -> None:
        """
        Downloads incident data to a CSV file.

        Args:
            incident_ids (list): List of incident IDs to download.
            file_path (str): Path to the CSV file. Defaults to 'tests/fetched_data/incident_data.csv'.

        Returns:
            None
        """
        try:
            logging.info("Downloading incident data to CSV.")

            # Fetch incidents based on provided incident ids
            incidents = Incident.objects.filter(id__in=incident_ids)

            # Define CSV header with incident ID and related article IDs
            header = ["Incident ID", "Related Article IDs"] + [
                "Published", "Title", "Summary", "System", "Time", "SEcauses", "NSEcauses",
                "Impacts", "Preventions", "Fixes", "ResponsibleOrg", "ImpactedOrg",
                "References", "Recurring Option", "Recurring Rationale", "Phase Option",
                "Boundary Option", "Nature Option", "Dimension Option", "Objective Option",
                "Intent Option", "Capability Option", "Duration Option", "Domain Option",
                "CPS Option", "Perception Option", "Communication Option", "Application Option",
                "Behaviour Option", "Phase Rationale", "Boundary Rationale", "Nature Rationale",
                "Dimension Rationale", "Objective Rationale", "Intent Rationale",
                "Capability Rationale", "Duration Rationale", "Domain Rationale", "CPS Rationale",
                "Perception Rationale", "Communication Rationale", "Application Rationale",
                "Behaviour Rationale"
            ]

            # Open CSV file and write header
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(header)

                # Write incident data
                for incident in incidents:
                    # Fetch related article IDs
                    related_article_ids = list(incident.articles.values_list('id', flat=True))

                    # Write row with incident ID and related article IDs
                    csv_writer.writerow([incident.id, related_article_ids] + [
                        incident.published, incident.title, incident.summary, incident.system,
                        incident.time, incident.SEcauses, incident.NSEcauses, incident.impacts,
                        incident.preventions, incident.fixes, incident.ResponsibleOrg,
                        incident.ImpactedOrg, incident.references, incident.recurring_option,
                        incident.recurring_rationale, incident.phase_option, incident.boundary_option,
                        incident.nature_option, incident.dimension_option, incident.objective_option,
                        incident.intent_option, incident.capability_option, incident.duration_option,
                        incident.domain_option, incident.cps_option, incident.perception_option,
                        incident.communication_option, incident.application_option,
                        incident.behaviour_option, incident.phase_rationale, incident.boundary_rationale,
                        incident.nature_rationale, incident.dimension_rationale, incident.objective_rationale,
                        incident.intent_rationale, incident.capability_rationale, incident.duration_rationale,
                        incident.domain_rationale, incident.cps_rationale, incident.perception_rationale,
                        incident.communication_rationale, incident.application_rationale,
                        incident.behaviour_rationale
                    ])

                logging.info(f"Incident data downloaded to CSV: {file_path}") 
                
        except Exception as e:
            logging.error(f"Error downloading article data to CSV: {str(e)}")
