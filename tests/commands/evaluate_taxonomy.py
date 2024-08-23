import argparse
import logging
import json
import textwrap
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
import csv

from failures.articles.models import Article, SearchQuery, Incident


class EvaluateTaxonomyCommand:
    # Define the file path for the manual dataset
    MANUAL_DATASET_FILE_PATH = "tests/ground_truth/interrater_agreement.csv"
    OUTPUT_FILE_PATH = "./tests/performance/taxonomy.csv"

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate taxonomy command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM at determining the taxonomy of a given article about software failure.
            If no arguments are provided, all articles that have been classified will be used to score performance.
            If --all is provided then more metrics will be outputted (# Right, # Wrong, # False Positive, # False Negative,
            # Evaluated).
            If --list is provided then a list of all articles that did not match will be outputted.
            If --articles is provided, then the list of articles input will be evaluated on their classification
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
        )
        parser.add_argument(
            "--saveCSV",
            action="store_true",
            help="Save metrics to a csv (saves to tests/performance/describes_failure.csv)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all articles incorrectly classified.",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """

        # Creating metrics to return
        metrics = {}

        # Store metrics
        metrics['Metrics'] = {
                'accuracy': 'accuracy',
                'precision': 'precision',
                'recall': 'recall',
                'f1_score': 'f1_score'
            }

        # Get list of correctly merged incidents
        auto_incident_set, man_incident_set = self.get_oto_ids()

        print(man_incident_set)

        # Get incidents
        incidents = Incident.objects.filter(id__in=auto_incident_set)
        
        # Define the file path
        input_file_path = EvaluateTaxonomyCommand.MANUAL_DATASET_FILE_PATH
        output_file_path = EvaluateTaxonomyCommand.OUTPUT_FILE_PATH

        # Mapping between Pandas column names and Django model field names
        column_to_field_mapping = {
            "Incident": "id",
            "Phase Option": "phase_option",
            "Boundary Option": "boundary_option",
            "Nature Option": "nature_option",
            "Dimension Option": "dimension_option",
            "Objective Option": "objective_option",
            "Intent Option": "intent_option",
            "Capability Option": "capability_option",
            "Duration Option": "duration_option",
            "Domain Option": "domain_option",
            "CPS Option": "cps_option",
            # "Perception Option": "perception_option",
            # "Communication Option": "communication_option",
            # "Application Option": "application_option",
            "Behaviour Option": "behaviour_option",
            "Recurring": "recurring_option"
        }

        # Define the columns to read
        columns_to_read = [
            # "id", # UPDATE WITH MANUAL
            "Incident",
            "Article IDs",
            # "Describes Failure", # Comment back in when manual set is complete
            # "Analyzable Failure", # Comment back in when manual set is complete
            "Phase Option",
            "Boundary Option",
            "Nature Option",
            "Dimension Option",
            "Objective Option",
            "Intent Option",
            "Capability Option",
            "Duration Option",
            "Domain Option",
            "CPS Option",
            "Recurring",
            # "Perception Option",
            # "Communication Option",
            # "Application Option",
            "Behaviour Option"
        ]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_csv(input_file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{input_file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # Rename columns using the mapping
        df.rename(columns=column_to_field_mapping, inplace=True)

        # Filter by incidents
        df = df[df['id'].apply(lambda x: x in man_incident_set)]

        # List of taxonomies to iterate over
        taxonomies = list(column_to_field_mapping.values())
        
        # Remove 'id' from taxonomies
        taxonomies.remove('id')

        for taxonomy in taxonomies:
            logging.info("evaluate_taxonomy: Evaluating %s for %d incidents", taxonomy, len(auto_incident_set))
            # Extract relevant column from the dataframe (and fill in NaN values as Unknown)
            df_taxonomy_values = df[taxonomy].fillna('unknown').tolist()
            # df_taxonomy_values = self.get_taxonomy_mapping(taxonomy, df_taxonomy_values)

            # Extract corresponding field values from the incidents (and fill in None values as Unknown)
            incidents_taxonomy_values = list(incidents.values_list(taxonomy, flat=True))
            incidents_taxonomy_values = ['unknown' if value is None else value for value in incidents_taxonomy_values]

            if not df_taxonomy_values or not incidents_taxonomy_values:
                logging.info("Insufficent values for %s", taxonomy)
                continue

            # print(df_taxonomy_values)
            # print("\n here \n")
            # print(incidents_taxonomy_values)
            # print("\n\n\n\n-----------------------------------------------------------\n\n\n\n\n")

            # incidents_taxonomy_values = [json.dumps(json.loads(value.replace("\n", ""))) for value in incidents_taxonomy_values]

            # print(incidents_taxonomy_values)
            # print("\n here \n")

            # json_format = json.loads(incidents_taxonomy_values[0]).copy()

            # for key, value in json_format.items():
            #     json_format[key] = False

            # df_taxonomy_values_updated = []
            # for value in df_taxonomy_values:
            #     value = [val.strip() for val in value.split(',')]
            #     json_copy = json_format.copy()

            #     for val in value:
            #         json_copy[val] = True

            #     df_taxonomy_values_updated.append(json.dumps(json_copy))

            # print(df_taxonomy_values_updated)

            # df_taxonomy_values = df_taxonomy_values_updated

            # return

            # Convert string labels to numeric format using LabelEncoder
            all_labels = set(df_taxonomy_values).union(set(incidents_taxonomy_values))
            label_encoder = LabelEncoder().fit(list(all_labels))
            print(len(df_taxonomy_values))
            print(len(incidents_taxonomy_values))
            ground_truth_encoded = label_encoder.transform(df_taxonomy_values)
            predictions_encoded = label_encoder.transform(incidents_taxonomy_values)

            # Calculate additional metrics
            accuracy = accuracy_score(predictions_encoded, ground_truth_encoded)
            precision = precision_score(predictions_encoded, ground_truth_encoded, average='weighted', zero_division=1)
            recall = recall_score(predictions_encoded, ground_truth_encoded, average='weighted', zero_division=1)
            f1 = f1_score(predictions_encoded, ground_truth_encoded, average='weighted', zero_division=1)

            # Log the confusion matrix and additional metrics
            logging.info("Accuracy for %s: %.4f (%.2f%%)", taxonomy, accuracy, accuracy * 100)
            logging.info("Precision for %s: %.4f (%.2f%%)", taxonomy, precision, precision * 100)
            logging.info("Recall for %s: %.4f (%.2f%%)", taxonomy, recall, recall * 100)
            logging.info("F1 Score for %s: %.4f (%.2f%%)", taxonomy, f1, f1 * 100)

            # Store the confusion matrix as needed
            metrics[taxonomy] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }

        if args.saveCSV:
            # Store metrics in a CSV
            logging.info(f"Storing metrics in: {output_file_path}")
            metrics_df = pd.DataFrame(metrics)
            metrics_df.to_csv(output_file_path, index=False)

        # Return the metrics
        return metrics

    def get_oto_ids(self):
        """
        Get a list of Django incident IDs that have a one-to-one mapping of article IDs to the manual dataset.

        Returns:
            list: List of Django incident IDs.
        """
        # Define the file path for the manual dataset
        manual_dataset_file_path = EvaluateTaxonomyCommand.MANUAL_DATASET_FILE_PATH

        # Define the column name in the manual dataset
        manual_dataset_column_name = "Article IDs"

        # Read the manual dataset into a Pandas DataFrame
        try:
            manual_df = pd.read_csv(manual_dataset_file_path, usecols=[manual_dataset_column_name])
            logging.info("Manual dataset loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{manual_dataset_file_path}' was not found.")
            return []

        # Filter out rows with NaN values in the specified column
        manual_df = manual_df.dropna(subset=[manual_dataset_column_name])

        # Flatten the list of article IDs
        article_ids = manual_df[manual_dataset_column_name].tolist()

        # Convert to sets of ids
        article_ids_sets = [set(map(int, str(item).split('; '))) if isinstance(item, str) else {item} for item in article_ids]

        # List of one-to-one incident ids to return
        auto_incident_ids = []
        man_incident_ids = []

        # Iterate through and find one to one incidents
        for i, article_set in enumerate(article_ids_sets):

            # Check for None
            if not article_ids_sets:
                continue

            # Get incident ids of article set
            incident_ids = list(
                Article.objects.filter(id__in=article_set)
                .exclude(incident__isnull=True)
                .values_list('incident_id', flat=True)
                .distinct()
            )

            # Ensure all articles map to the same incident
            if len(incident_ids) != 1:
                continue
            
            incident_ids = incident_ids[0]

            # Get set of articles related to incident id
            auto_articles_set = set(
                Article.objects.filter(incident__id=incident_ids)
                .exclude(incident__isnull=True)
                .values_list('id', flat=True)
                .distinct()
            )

            # Compare sets
            if auto_articles_set == article_set:
                auto_incident_ids.append(incident_ids)
                man_incident_ids.append(i + 1)
                
        return auto_incident_ids, man_incident_ids

    def get_taxonomy_mapping(self, taxonomy: str, values: list):
        pass
        # TODO: Commented out until working
    #     """
    #     Returns the mapping of the string taxonomy values to the integer taxonomy values.

    #     Args:
    #         taxonomy (String): The taxonomy being evaluated
    #         values (list): The values stored in the database for the incidents.

    #     """
    #     taxonomy_mapping = {
    #         'phase_option': {
    #             0: 'system design',
    #             1: 'operation',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'boundary_option': {
    #             0: 'within the system',
    #             1: 'outside the system',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'nature_option': {
    #             0: 'human actions',
    #             1: 'non-human actions',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'dimension_option': {
    #             0: 'hardware',
    #             1: 'software',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'objective_option': {
    #             0: 'malicious',
    #             1: 'non-malicious',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'intent_option': {
    #             0: 'deliberate',
    #             1: 'accidental',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'capability_option': {
    #             0: 'accidental',
    #             1: 'development incompetence',
    #             2: 'both',
    #             3: 'neither',
    #             -1: 'unknown',
    #         },
    #         'duration_option': {
    #             0: 'Permanent',
    #             1: 'Transient Intermittent',
    #             2: 'neither',
    #             -1: 'unknown',
    #         },
    #         'cps_option': {
    #             0: True,
    #             1: False,
    #             -1: 'unknown',
    #         },
    #         'communication_option': {
    #             0: False,
    #             1: 'link level',
    #             2: 'connectivity level',
    #             -1: 'unknown',
    #         },
    #         'application_option': {
    #             0: True,
    #             1: False,
    #             -1: 'unknown',
    #         },
    #     }
    #         'behaviour_option': {
    #             0: 'crash',
    #             1: 'omission',
    #             2: 'timing',
    #             3: 'value',
    #             4: 'byzantine fault',
    #             5: 'Other',
    #             -1: 'unknown',
    #         },
    #         'domain_option': {
    #             0: 'information',
    #             1: 'transportation',
    #             2: 'natural resources',
    #             3: 'sales',
    #             4: 'construction',
    #             5: 'manufacturing',
    #             6: 'utilities',
    #             7: 'finance',
    #             8: 'knowledge',
    #             9: 'health',
    #             10: 'entertainment',
    #             11: 'government',
    #             12: 'other',
    #             -1: 'unknown',
    #         },
    #         'consequence_option': {
    #             0: 'death',
    #             1: 'harm',
    #             2: 'basic',
    #             3: 'property',
    #             4: 'delay',
    #             5: 'non-human',
    #             6: 'no consequence',
    #             7: 'theoretical consequences',
    #             8: 'other',
    #             -1: 'unknown',
    #         },
    #         'perception_option': {
    #             0: 'sensors',
    #             1: 'actuators',
    #             2: 'processing unit',
    #             3: 'network communication',
    #             4: 'embedded software combination',
    #             5: False,
    #             -1: 'unknown',
    #         }
    #     }

    #     mapped_values = [taxonomy_mapping[taxonomy][value] for value in values]

    #     return mapped_values


