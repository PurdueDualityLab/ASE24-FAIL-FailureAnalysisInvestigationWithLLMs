from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
import argparse
import logging
import textwrap
import pandas as pd

from failures.articles.models import Article_Ko, SearchQuery


class EvaluateMergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM at merging the articles into clusters of incidents. This will return
            a V-Measure which is a harmonic mean between a homogeneity score and a completeness score. If no arguments are
            provided, all articles that have a corresponding manual classificaiton will be used to score performacne and only
            V-Measure will be logged.
            If --all is provided then more metrics will be output (V-Measure, Homogeneity Score, Completeness Score, etc.)
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Create dictionary to store metrics
        metrics = {
            "Homogeneity": 0,
            "Completeness": 0,
            "V-Measure": 0
        }

        # Define the file path
        # input_file_path = "./tests/ko_test/data/Ko_Stories_Consensus.csv"
        # TODO: add input path as interrater agreement csv. Then read the files in using the storyID and the articleID, then compare
        input_file_path = "tests/ko_test/data/Ko_Stories_Consensus.csv"
        output_file_path = "tests/ko_test/performance/merge_consensus.csv"

        # Define the columns to read
        columns_to_read = ["storyID", "articleID", "Consensus"]

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

        # Filter rows where 'Consensus' is 'relevant'
        df = df[df['Consensus'] == 'relevant']

        # Get the article ids
        article_ids = self.get_article_ko_ids(df)

        # Query for articles matching manual db IDs
        matching_articles = Article_Ko.objects.filter(id__in=article_ids.keys())

        # Map id to incident for ground truth and predicted
        ground_truth_mapping = article_ids
        predicted_mapping = {article.id: article.incident.id for article in matching_articles if article.incident}

        # Get common ids
        common_ids = set(ground_truth_mapping.keys()) & set(predicted_mapping.keys())

        # Create lists for true labels and predicted labels based on common IDS
        true_labels = [ground_truth_mapping[article_id] for article_id in common_ids]
        predicted_labels = [predicted_mapping[article_id] for article_id in common_ids]

        # Calculate homogeneity, completeness, and V-Measure
        if common_ids:
            # Calculate homogeneity score
            homogeneity = homogeneity_score(true_labels, predicted_labels)

            # Calculate completeness score
            completeness = completeness_score(true_labels, predicted_labels)

            # Calculate V-measure
            v_measure = v_measure_score(true_labels, predicted_labels)

            # Log results
            logging.info(f"Homogeneity Score: {homogeneity:.2f}")
            logging.info(f"Completeness Score: {completeness:.2f}")
            logging.info(f"V-Measure Score: {v_measure:.2f}")

            # Store metrics
            metrics["Homogeneity"] = homogeneity
            metrics["Completeness"] = completeness
            metrics["V-Measure"] = v_measure

            # Finding some additional metrics
            ground_truth_set = set(true_labels)
            predicted_set = set(predicted_labels)
            metrics["Articles evaluated"] = len(common_ids)
            metrics["Number of ground truth stories"] = len(ground_truth_set)
            metrics["Number of predicted stories"] = len(predicted_set)
        else:
            logging.info("Evaluate Merge Command: No common IDs found between ground truth and predicted data.")

        # Convert metrics dictionary to a Pandas DataFrame
        metrics_df = pd.DataFrame(metrics, index=[0])

        # Save the DataFrame to a CSV file
        metrics_df.to_csv(output_file_path, index=False)
        logging.info(f"Metrics saved to {output_file_path}")


        return metrics

    def get_article_ko_ids(self, df: pd.DataFrame) -> dict:

        ids = {}

        # Iterate through dataframe
        for index, row in df.iterrows():
            
            # Get article_ko id
            article_ko_instance = Article_Ko.objects.filter(storyID=row['storyID'], articleID=row['articleID'])

            if not article_ko_instance:
                continue
        
            ids[article_ko_instance[0].id] = row['storyID']

        return ids