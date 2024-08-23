import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import QUESTIONS, FAILURE_SYNONYMS, TAXONOMY_OPTIONS

class PostmortemArticleCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the postmortem command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Create postmortems for articles that report on SE failures present in the database. If no arguments are provided, create postmortems for all
            SE failure articles that do not have a postmortem; otherwise, if --all is provided, create postmortems for all
            SE failure articles. If an article does not have a body, a postmortems will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create postmortems for all articles even if they already have a postmortem.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key for all articles.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the postmortem creation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        logging.info("\nCreating postmortems for articles.")

        query_all = args.all
        query_key = args.key

        # Define a queryset of articles for postmortem creation
        queryset = (
            Article.objects.filter(
                describes_failure=True,
                #headline__icontains='Boeing'
            )
        )

        questions = QUESTIONS       
        taxonomy_options = TAXONOMY_OPTIONS

        if query_key != 'None':
            questions = questions[query_key]
            ### THIS IS INCORECT, TAKE A LOOK AT postmortemIncidentAutoVDB.py


        # Create a mapping of questions to ChatGPT prompts
        questions_chat = {}
        for question_key in questions.keys():
            if "option" in questions[question_key]:
                questions_chat[question_key] = questions[question_key] + "\nRETURN ANSWER IN JSON FORMAT: {\"explanation\": \"explanation\", \"option\": \"option number\"}. Don't provide anything outside the format."
            #elif "word" or "words" in questions[question_key]:
            #    questions_chat[question_key] = questions[question_key]


        
        
        # Initialize ChatGPT model
        chatGPT = ChatGPT()
        inputs = {"model": "gpt-3.5-turbo", "temperature": 1}

        successful_failure_creations = 0
        for article in queryset:
            if article.body == "" or article.describes_failure is not True:
                logging.info("Article is empty or does not describe failure %s.", article)
                continue
            logging.info("Creating postmortem for article %s.", article)
            article.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, taxonomy_options, args.all, args.key)
            logging.info("Succesfully created postmortem for article %s.", article)
            successful_failure_creations += 1

        logging.info("Successfully created postmortems for %d articles.", successful_failure_creations)
