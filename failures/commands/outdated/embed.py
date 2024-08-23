import argparse
import logging
import textwrap

from failures.articles.models import Article
from failures.networks.models import Embedder


class EmbedCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the embed command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Create embeddings for articles present in the database. If no arguments are provided, create embeddings for all
            articles that do not have an embedding; otherwise, if --all is provided, create embeddings for all
            articles. If an article does not have a body, an embedding will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Create embeddings for all articles even if they already have an embedding.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the embedding creation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        # Initialize the embedder for creating embeddings
        embedder = Embedder()

        # Determine the queryset of articles to embed on the provided arguments
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(embedding=None)
        )

        successful_embeddings = 0

        #Loop through articles and create embeddings
        for article in queryset:
            logging.info("Embedding %s.", article)
            
            # Skip articles without a body
            if article.body == "":
                continue

            # Create embedding for the article
            article.create_embedding(embedder)
            successful_embeddings += 1

        logging.info("Successfully created embeddings for %d articles.", successful_embeddings)
