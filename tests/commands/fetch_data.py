import argparse
import logging
import textwrap
import csv

from failures.articles.models import Article, Incident


class FetchDataCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            The function fetches data from the failures database.
            """
        )
        parser.add_argument(
            "--ids",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="Ids of data stored in failures database.",
            required=True,
        )
        parser.add_argument(
            "--option",
            type=int,
            help="What information to fetch. 1 = Articles (--ids = article_ids), 2 = Incidents (--ids = incident_ids), 3 = Articles (--ids = incident_ids), 4 = Incidents (--ids = article_ids)",
            required=True,
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        This command fetches articles and incidents as needed.     

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        logging.info(f"Fetching data.")

        # Route to correct option
        option = args.option
        ids = args.ids

        if option == 1:
            # Fetch articles based on provided article ids
            logging.info(f"Fetching articles with ids: {ids}")
            articles = Article.objects.filter(id__in=ids)
            self.download_article_data_to_csv(articles)
        elif option == 2:
            # Fetch incidents based on provided incident ids
            logging.info(f"Fetching incidents with ids: {ids}")
            incidents = Incident.objects.filter(id__in=ids)
            self.download_incident_data_to_csv(incidents)
        elif option == 3:
            # Fetch articles based on provided incident ids
            logging.info(f"Fetching articles with incident ids: {ids}")
            articles = Article.objects.filter(incident__id__in=ids)
            self.download_article_data_to_csv(articles)
        elif option == 4:
            # Fetch incidents based on provided article ids
            logging.info(f"Fetching incidents with article ids: {ids}")
            incidents = Incident.objects.filter(articles__id__in=ids, experiment=True)
            self.download_incident_data_to_csv(incidents)
        else:
            logging.error("Invalid sample option. Please provide a valid option (1, 2, 3, or 4).")


    def download_incident_data_to_csv(self, incident_ids: list, file_path: str = 'tests/fetched_data/incident_data.csv') -> None:
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
                "Published", "Title", "Summary", "Time", "System", "ResponsibleOrg", "ImpactedOrg", "SEcauses", "NSEcauses",
                "Impacts", "Preventions", "Fixes", 
                "References", "Recurring Option", "Phase Option",
                "Boundary Option", "Nature Option", "Dimension Option", "Objective Option",
                "Intent Option", "Capability Option", "Duration Option", "Behaviour Option", "Domain Option", "Consequence Option", 
                "CPS Option", "Perception Option", "Communication Option", "Application Option",
                "Recurring Rationale", "Phase Rationale", "Boundary Rationale", "Nature Rationale",
                "Dimension Rationale", "Objective Rationale", "Intent Rationale",
                "Capability Rationale", "Duration Rationale", "Behaviour Rationale", "Domain Rationale", "Consequence Rationale", "CPS Rationale",
                "Perception Rationale", "Communication Rationale", "Application Rationale",
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
                        incident.published, incident.title, incident.summary, incident.time, incident.system, 
                        incident.ResponsibleOrg, incident.ImpactedOrg, 
                        incident.SEcauses, incident.NSEcauses, incident.impacts,
                        incident.preventions, incident.fixes, incident.references, incident.recurring_option,
                        incident.phase_option, incident.boundary_option,
                        incident.nature_option, incident.dimension_option, incident.objective_option,
                        incident.intent_option, incident.capability_option, incident.duration_option, incident.behaviour_option,
                        incident.domain_option, incident.consequence_option, incident.cps_option, incident.perception_option,
                        incident.communication_option, incident.application_option,
                        incident.recurring_rationale, incident.phase_rationale, incident.boundary_rationale,
                        incident.nature_rationale, incident.dimension_rationale, incident.objective_rationale,
                        incident.intent_rationale, incident.capability_rationale, incident.duration_rationale, incident.behaviour_rationale,
                        incident.domain_rationale, incident.consequence_rationale, incident.cps_rationale, incident.perception_rationale,
                        incident.communication_rationale, incident.application_rationale,
                    ]) 

            logging.info(f"Incident data downloaded to CSV: {file_path}")

        except Exception as e:
            logging.error(f"Error downloading incident data to CSV: {str(e)}")

    def download_article_data_to_csv(self, article_ids: list, file_path: str = 'tests/fetched_data/article_data.csv') -> None:
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