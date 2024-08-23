import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, SearchQuery


class EvaluateIdentificationCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate classification command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM predicting whether or not a given article is a software failure.
            If no arguments are provided, all articles that have been classified will be used to score performance.
            If --all is provided then more metrics will be outputted (# Right, # Wrong, # False Positive, # False Negative,
            # Evaluated).
            If --list is provided then a list of all articles that did not match will be outputted.
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
            help="Save metrics to a csv (saves to tests/performance/analyzable_failure.csv)",
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
        logging.info("\n\nNow evaluating ANALYZE FAILURES\n")
        metrics = {}
        
        # Define the file paths
        input_file_path = "./tests/ground_truth/ground_truth_classify.xlsx"
        output_file_path = "./tests/performance/analyzable_failure.csv"

        # Define the columns to read
        columns_to_read = ["id", "failure", "analyzable"]

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

        # Filter rows where 'id' is not a positive integer and 'failure?' is not 0 or 1
        df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]
        df = df[df['failure'] == True]

        # Check --articles
        if args.articles:
            df = df[df['id'].apply(lambda x: x in args.articles)]
            df = df[df['failure'] == True]

        # Get a list of article IDs from the manual database
        article_ids = df['id'].tolist()

        # Query for articles matching manual db IDs
        matching_articles = Article.objects.filter(id__in=article_ids)

        # Calculate accuracy and additional metrics
        total_match = 0
        total_articles = len(matching_articles)
        false_positives = 0
        false_negatives = 0
        true_positives = 0
        true_negatives = 0

        # List of incorrectly classified articles (if --list)
        incorrectly_classified_articles = []

        # Iterate through articles and count matches
        for article in matching_articles:
            article_id = article.id
            ground_truth = df[df['id'] == article.id]['analyzable'].values[0]
            if article.analyzable_failure != None and article.analyzable_failure == ground_truth:
                total_match += 1
                if article.analyzable_failure:
                    true_positives += 1
                else:
                    true_negatives += 1
            else:
                if args.list:
                    incorrectly_classified_articles.append((
                        f"Article ID: {article.id}, "
                        f"Title: {article.headline}, "
                        f"Ground Truth: {'Enough info' if ground_truth == 1 else 'Not enough info'}, "
                        f"Classified As: {'Enough info' if article.analyzable_failure != None and article.analyzable_failure == 1 else 'Not enough info'}",
                        ground_truth
                    ))
                # If --all then update false positives and negatives
                # if args.all:
                if article.analyzable_failure != None and article.analyzable_failure == 1 and ground_truth == 0:
                    false_positives += 1
                elif article.analyzable_failure != None and article.analyzable_failure == 0 and ground_truth == 1:
                    false_negatives += 1

        # Checking to see if there are any matching articles
        if total_articles > 0:
            accuracy_percentage = (total_match / total_articles) * 100
            logging.info(f"Accuracy: {accuracy_percentage:.2f}% ({total_match}/{total_articles})")

            # # Checking if --list
            # if args.list:
            #     logging.info('List of incorrectly classified articles:')
            #     for article in incorrectly_classified_articles:
            #         logging.info(article[0])

            # Checkign if --all
            # if args.all:
            # Calculate false positive and false negative rates as both fractions and percentages
            false_positive_rate = (false_positives / total_articles) * 100
            false_negative_rate = (false_negatives / total_articles) * 100
            false_positive_fraction = f"{false_positives}/{total_articles}"
            false_negative_fraction = f"{false_negatives}/{total_articles}"

            # Calculate the number and percentage of correct and wrong classifications
            correct_classifications = total_match
            wrong_classifications = total_articles - total_match
            wrong_percentage = (wrong_classifications / total_articles) * 100

            logging.info(f"False Positives: {false_positive_rate:.2f}% ({false_positive_fraction})")

            # Print out all false positives
            if args.list:
                logging.info('List of all false positive identifications:')
                for article in incorrectly_classified_articles:
                    if article[1] == 0:
                        logging.info(article[0])

            logging.info(f"False Negatives: {false_negative_rate:.2f}% ({false_negative_fraction})")

            # Print out all false positives
            if args.list:
                logging.info('List of all false negative identifications:')
                for article in incorrectly_classified_articles:
                    if article[1] == 1:
                        logging.info(article[0])

            logging.info(f"Wrong: {wrong_percentage:.2f}% ({wrong_classifications}/{total_articles})")
            logging.info(f"Total Evaluated: {total_articles}")

            metrics = {
                "Identify: Accuracy (Percentage)": f"{accuracy_percentage:.2f}%",
                "Identify: Accuracy (Fraction)": f"{total_match}/{total_articles}",
                "Identify: False Positive (Percentage)": f"{false_positive_rate:.2f}%",
                "Identify: False Positive (Fraction)": f"{false_positive_fraction}",
                "Identify: False Negative (Percentage)": f"{false_negative_rate:.2f}%",
                "Identify: False Negative (Fraction)": f"{false_negative_fraction}",
                "Identify: Wrong (Percentage)": f"{wrong_percentage:.2f}%",
                "Identify: Wrong (Fraction)": f"{wrong_classifications}/{total_articles}",
                "Identify: Total Evaluated": str(total_articles) 
            }

            # Calculate false positive and false negative rates as percentages
            fpr = (false_positives / (false_positives + true_negatives)) * 100
            fnr = (false_negatives / (false_negatives + true_positives)) * 100

            # Adding false positive and false negative rates to the metrics dictionary
            metrics["Identify: False Positive Rate (Percentage)"] = f"{fpr:.2f}%"
            metrics["Identify: False Negative Rate (Percentage)"] = f"{fnr:.2f}%"

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
            logging.info("Evaluate Identification Command: No common IDs found between ground truth and predicted data.")

        return metrics
