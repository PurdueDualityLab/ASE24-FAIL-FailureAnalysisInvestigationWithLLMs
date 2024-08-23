import argparse
import logging
import textwrap

from datetime import datetime
import csv

from failures.articles.models import Article, Incident
from django.db.models import Count


class StatsCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Report stats from the database.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Report stats for all articles in database.",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Report stats for articles published in a specific year in database.",
        )
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="To cluster incidents between 2010 and 2022 for experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nReporting Stats.")

        query_all = args.all
        query_year = args.year

        if query_year != None:
            years = [query_year]
        elif args.experiment is True:
            start_year = 2010
            end_year = 2022

            years = [year for year in range(start_year, end_year + 1)]

        else:
            years = list(Article.objects.values_list('published__year', flat=True).distinct())

        stats = {}
        for year in years:
            count_all = Article.objects.filter(published__year=year).count()
            count_scrape_successful = Article.objects.filter(scrape_successful=True, published__year=year).count()
            count_describes_failure = Article.objects.filter(describes_failure=True, published__year=year).count()
            count_analyzable_failure = Article.objects.filter(analyzable_failure=True, published__year=year).count()

            # Count incidents with articles for the specific year
            count_incidents = Incident.objects.filter(published__year=year).count() #Incident.objects.filter(articles__published__year=year).distinct().count()

            stats[year] = {
                'all': count_all,
                'scrape_successful': count_scrape_successful,
                'describes_failure': count_describes_failure,
                'analyzable_failure': count_analyzable_failure,
                'incidents': count_incidents
            }


        csv_file_path = 'results/stats.csv'
        # Write the data to the CSV file
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['Year', 'All', 'Scrape Successful', 'Describes Failure', 'Analyzable Failure', 'Incidents']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data
            for year, counts in stats.items():
                writer.writerow({
                    'Year': year,
                    'All': counts['all'],
                    'Scrape Successful': counts['scrape_successful'],
                    'Describes Failure': counts['describes_failure'],
                    'Analyzable Failure': counts['analyzable_failure'],
                    'Incidents': counts['incidents']
                })

        logging.info(f'Stats has been written to {csv_file_path}')

        


            

        


        