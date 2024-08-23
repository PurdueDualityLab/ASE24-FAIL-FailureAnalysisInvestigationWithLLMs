import argparse
import logging
import textwrap

from failures.articles.models import Article, SearchQuery


class ScrapeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the scrape command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Scrape articles from Google News RSS feeds. If no arguments are provided, use all search
            queries present in the database; otherwise, use the provided arguments to create a new search query.
            """
        )

        # Define command-line arguments for specifying search criteria
        parser.add_argument(
            "--keyword",
            type=str,
            help="Keyword to use for searching for news articles.",
        )
        parser.add_argument(
            "--start-year",
            type=int,
            help="News articles will be searched from this year onwards. This argument is optional.",
        )
        parser.add_argument(
            "--end-year",
            type=int,
            help="News articles will be searched until this year. This argument is optional.",
        )
        parser.add_argument(
            "--start-month",
            type=int,
            help="News articles will be searched from this month onwards. This argument is optional.",
        )
        parser.add_argument(
            "--end-month",
            type=int,
            help="News articles will be searched until this month. This argument is optional.",
        )
        parser.add_argument(
            "--sources",
            type=str,
            nargs="+",
            help="Sources to search for news articles, such as 'wired.com' or 'wired.com,nytimes.com'. "
            "This argument is optional.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Scrape all articles even if they already have a body.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article scraping process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """

        logging.info("\nScraping articles")
        
        if args.keyword:
            # Create a new search query based on the provided arguments
            search_query = SearchQuery.objects.create(
                keyword=args.keyword,
                start_year=args.start_year,
                end_year=args.end_year,
                start_month=args.start_month,
                end_month=args.end_month,
                sources=args.sources,
            )
            search_queries = [search_query]
        else:
            search_queries = SearchQuery.objects.all()

        

        for search_query in search_queries:
            logging.info("Collected articles for search query %s.", search_query)
            articles = Article.create_from_google_news_rss_feed(
                search_query=search_query
            )
            logging.info(
                "Scraped %s articles from search query %s.", len(articles), search_query
            )
            successful_body_scrapes = 0
            existing_body_scrapes = 0
            for article in articles:
                if article.body and not args.all:
                    # Skip articles with existing bodies if not using the --all flag
                    existing_body_scrapes += 1
                    continue
                if article.scrape_body():
                    # Scrape the body of the article
                    successful_body_scrapes += 1

            if not args.all:
                logging.info(
                    "Scraped the body of %s articles from search query %s. %s articles already had a body.",
                    successful_body_scrapes,
                    search_query,
                    existing_body_scrapes,
                )
            else:
                logging.info(
                    "Scraped the body of %s articles from search query %s.",
                    successful_body_scrapes,
                    search_query,
                )
