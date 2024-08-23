from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, SearchQuery


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
        # Create dictionary to store metrics
        metrics = {}

        # Define the file paths
        input_file_path = "./tests/ground_truth/ground_truth_classify.xlsx"
        output_file_path = "./tests/performance/merge.csv"

        # Define the columns to read
        columns_to_read = ["id", "incident"]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_excel(input_file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{input_file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # Filter rows where 'id' is not a positive integer and 'Describes Failure?' is not 0 or 1
        df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]
        df = df[df['incident'].apply(lambda x: isinstance(x, float) and x >= 0)]

        # Check --articles
        if args.articles:
            df = df[df['id'].apply(lambda x: x in args.articles)]

        # Get a list of article IDs from the manual database
        article_ids = df['id'].tolist()

        # Query for articles matching manual db IDs
        matching_articles = Article.objects.filter(id__in=article_ids, analyzable_failure=True)

        # Map id to incident for ground truth and predicted
        ground_truth_mapping = {row['id']: int(row['incident']) for _, row in df.iterrows()}
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
            if args.all:
                logging.info(f"Homogeneity Score: {homogeneity:.2f}")
                logging.info(f"Completeness Score: {completeness:.2f}")
            logging.info(f"V-Measure Score: {v_measure:.2f}")

            # Total number of articles and the number used
            total_articles = len(ground_truth_mapping.keys())
            used_articles = len(common_ids)

            # Store metrics
            metrics["Merge: Homogeneity"] = homogeneity
            metrics["Merge: Completeness"] = completeness
            metrics["Merge: V Measure"] = v_measure
            metrics["Merge: Percentage of Articles Used"] = f"{(used_articles / total_articles) * 100:.2f}%"
            metrics["Merge: Fraction of Articles Used"] = f"{used_articles}/{total_articles}"

            # # Get incorrect labels
            # ground_truth_reverse_mapping = {}
            # for _, row in df.iterrows():
            #     article_id = row['id']
            #     incident_id = int(row['incident'])
            #     if incident_id in ground_truth_reverse_mapping:
            #         ground_truth_reverse_mapping[incident_id].append(article_id)
            #     else:
            #         ground_truth_reverse_mapping[incident_id] = [article_id]

            # with open('tests/auto_evaluation/ground_to_pred_merge.csv', 'w', newline='') as csvfile:
            #     writer = csv.writer(csvfile)
            #     for key in ground_truth_reverse_mapping:
            #         curr_list = []
            #         for article in ground_truth_reverse_mapping[key]:
            #             curr_list.append((predicted_mapping[int(article)], article))
            #         incident = (key, curr_list)
            #         writer.writerow([incident[0]] + curr_list)

            # incident_article_mapping = {}
            # for article_id, incident_id in predicted_mapping.items():
            #     if incident_id in incident_article_mapping:
            #         incident_article_mapping[incident_id].append(article_id)
            #     else:
            #         incident_article_mapping[incident_id] = [article_id]

            # with open('tests/auto_evaluation/pred_to_ground_merge.csv', 'w', newline='') as csvfile:
            #     writer = csv.writer(csvfile)
            #     for key in incident_article_mapping:
            #         curr_list = []
            #         for article in incident_article_mapping[key]:
            #             curr_list.append((ground_truth_mapping[article], article))
            #         incident = (key, curr_list)
            #         writer.writerow([incident[0]] + curr_list)



            if args.saveCSV:
                logging.info(f"Storing metrics in: {output_file_path}")
                with open(output_file_path, mode='w', newline='') as csv_file:
                    fieldnames = metrics.keys()
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                    # Writing the header
                    writer.writeheader()

                    # Writing the metrics
                    writer.writerow(metrics)
        else:
            logging.info("Evaluate Merge Command: No common IDs found between ground truth and predicted data.")

        return metrics
