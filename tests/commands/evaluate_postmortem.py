import argparse
import logging
import textwrap
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import openai

from failures.articles.models import Article, SearchQuery, Incident

class EvaluatePostmortemCommand:
    # Define the file path for the manual dataset
    MANUAL_DATASET_FILE_PATH = "./tests/manual_evaluation/experiment_data_manual_articles_Analyst-B.xlsx"  # UPDATE

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate postmortem command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM to construct a postmortem. This evaluation uses ChatGPT to 
            evaluate model outputs with reference to the manual answers. 
            If no arguments are provided, all articles that have been classified and postmortems created will be used
            to score performance. 
            If --list is provided then a list of all articles that did not match will be outputted


            Evaluate the performance of the LLM predicting whether or not a given article is a software failure.
            If no arguments are provided, all articles that have been classified will be used to score performance.
            If --all is provided then more metrics will be outputted (# Right, # Wrong, # False Positive, # False Negative,
            # Evaluated).
            If --articles is provided then a only the list of articles provided will be evaluated
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
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
        metrics = {}

        # Store metrics
        metrics['Metrics'] = {
            'invalid': 'invalid',
            'disjoint': 'disjoint',
            'equal': 'equal',
            'subset': 'subset',
            'superset': 'superset',
            'overlapping': 'overlapping'
            }

        # Get list of correctly merged incidents
        auto_incident_set, man_incident_set = self.get_oto_ids()

        # Get incidents
        incidents = Incident.objects.filter(id__in=auto_incident_set)
        
        # Define the file path
        file_path = EvaluatePostmortemCommand.MANUAL_DATASET_FILE_PATH

        # Mapping between Pandas column names and Django model field names
        column_to_field_mapping = {
            "Incident ID": "id",
            "System": "system",
            "Time": "time",
            "SEcauses": "SEcauses",
            "NSEcauses": "NSEcauses",
            "Impacts": "impacts",
            "Mitigations": "mitigations",
            "ResponsibleOrg": "ResponsibleOrg",
            "ImpactedOrg": "ImpactedOrg",
            "Sources": "references",
        }

        # Define the columns to read
        columns_to_read = [
            "Incident ID",
            "System",
            "Time",
            "SEcauses",
            "NSEcauses",
            "Impacts",
            "Mitigations",
            "ResponsibleOrg",
            "ImpactedOrg",
            "Sources",
        ]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_excel(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # Rename columns using the mapping
        df.rename(columns=column_to_field_mapping, inplace=True)

        # Filter rows where 'id' is not a positive integer and 'Describes Failure?' is not 0 or 1 #UPDATE
        df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]

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

            # Extract corresponding field values from the incidents (and fill in None values as Unknown)
            incidents_taxonomy_values = list(incidents.values_list(taxonomy, flat=True))
            incidents_taxonomy_values = ['unknown' if value is None else value for value in incidents_taxonomy_values]

            # Calculate additional metrics
            # accuracy = accuracy_score(incidents_taxonomy_values, df_taxonomy_values)
            # precision = precision_score(incidents_taxonomy_values, df_taxonomy_values, average='weighted', zero_division=1)
            # recall = recall_score(incidents_taxonomy_values, df_taxonomy_values, average='weighted', zero_division=1)
            # f1 = f1_score(incidents_taxonomy_values, df_taxonomy_values, average='weighted', zero_division=1)
            count = [0] * 6

            for answer, expert in zip(incidents_taxonomy_values, df_taxonomy_values):
                resp = self.evaluate_model_output(answer, expert)
                count[resp['type_of_overlap']] += 1

                # Logging statements
                logging.info("Answer: %s", answer)
                logging.info("Expert Answer: %s", expert)
                logging.info("Type of Overlap: %s", resp["type_of_overlap"])
                logging.info("Overlap Reason: %s", resp['overlap_reason'])
                logging.info("Contradiction Reason: %s", resp['contradiction_reason'])

            count = [x / len(incidents_taxonomy_values) for x in count]

            # Store the confusion matrix as needed
            metrics[taxonomy] = {
                'invalid': count[0],
                'disjoint': count[1],
                'equal': count[2],
                'subset': count[3],
                'superset': count[4],
                'overlapping': count[5]
            }

        # Store metrics in a CSV
        metrics_df = pd.DataFrame(metrics)
        metrics_df.to_csv('./tests/performance/postmortem.csv', index=False)

        # Return the metrics
        return metrics

    def get_oto_ids(self):
        """
        Get a list of Django incident IDs that have a one-to-one mapping of article IDs to the manual dataset.

        Returns:
            list: List of Django incident IDs.
        """
        # Define the file path for the manual dataset
        manual_dataset_file_path = EvaluatePostmortemCommand.MANUAL_DATASET_FILE_PATH

        # Define the column name in the manual dataset
        manual_dataset_column_name = "Article IDs"

        # Read the manual dataset into a Pandas DataFrame
        try:
            manual_df = pd.read_excel(manual_dataset_file_path, usecols=[manual_dataset_column_name])
            logging.info("Manual dataset loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{manual_dataset_file_path}' was not found.")
            return []

        # Filter out rows with NaN values in the specified column
        manual_df = manual_df.dropna(subset=[manual_dataset_column_name])

        # Flatten the list of article IDs
        article_ids = manual_df[manual_dataset_column_name].tolist()

        # Convert to sets of ids
        article_ids_sets = [set(map(int, str(item).split(', '))) if isinstance(item, str) else {item} for item in article_ids]

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
                man_incident_ids.append(i)
                

        return auto_incident_ids, man_incident_ids

    def evaluate_model_output(self, answer, expert_answer):
        """
        Evaluate the model output with reference to gold-standard answers using ChatGPT API.

        Args:
            answer (str): Model-generated answer.
            expert_answer (str): Gold-standard answer.

        Returns:
            dict: JSON object containing information about the evaluation.
        """

        # openai.api_key = "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"
        openai.api_key = os.getenv('OPENAI_API_KEY')

        result = {
            "type_of_overlap": None,
            "overlap_reason": None,
            "contradiction_reason": None
        }

        # Step 1: Reason about the type of overlap using ChatGPT
        prompt = f"Respond with just the number to indicate the relationship between the information in the submitted answer and the expert answer: disjoint (1), equal (2), subset (3), superset (4), or overlapping (5). Answer: {answer} Expert Answer: {expert_answer}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=1
        )
        result["type_of_overlap"] = response['choices'][0]['message']['content'].strip()
        type_of_overlap = result["type_of_overlap"]

        # Save as integer
        try:
            result["type_of_overlap"] = int(result["type_of_overlap"])
        except ValueError:
            result["type_of_overlap"] = 0

        prompt = f"Reason step-by-step about why the information in the submitted answer compared to the expert answer is {type_of_overlap}. Answer: {answer} Expert Answer: {expert_answer}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=100
        )
        result["overlap_reason"] = response['choices'][0]['message']['content'].strip()

        # Step 2: Reason about contradiction using ChatGPT
        prompt = f"Reason step-by-step about whether the submitted answer contradicts any aspect of the expert answer. Submitted Answer: {answer} Expert Answer: {expert_answer}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=100
        )
        result["contradiction_reason"] = response['choices'][0]['message']['content'].strip()

        return result
