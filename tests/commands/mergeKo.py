import argparse
import logging
import textwrap

from datetime import timedelta
import networkx as nx

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT,  ClassifierChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import QUESTIONS, FAILURE_SYNONYMS

class MergeKoCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Merge postmortems for articles that report on SE failures present in the database. If no arguments are provided, 
            only new articles will be merged into incidents; otherwise, if --all is provided, all articles will be remerged
            into new incidents. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Redo incident merging for all articles that describe SE failures.",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--temp",
            type=float,
            default=-1,
            help="Sets the temperature for ChatGPT",
        )


    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the incident merging process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        if args.articles:
            logging.info("Merge: Setting incidents for testing set equal to null.")
            articles = (
                # Article.objects.filter(describes_failure=True, analyzable_failure=True, incident__isnull=True, id__in=args.articles)
                Article.objects.filter(describes_failure=True, analyzable_failure=True, id__in=args.articles).order_by('published') # Removed incident__isnull=True
            )
            articles.update(incident=None)
        else:
            logging.info("KoMerge: Experiment set of articles not provided")

        # Create a dictionary to map article IDs to Article objects
        articles_dict = {article.id: article for article in articles}

        graph = nx.DiGraph()

        for i, article1 in enumerate(articles_dict.values()):

            window = 7
            graph.add_node(article1.id)

            for article2 in list(articles_dict.values())[i + 1:]:
                if (article2.published - article1.published).days <= window:
                    if self.calculate_tfidf_similarity(article1.body, article2.body) >= 0.25:
                        graph.add_edge(article1.id, article2.id)
                        window = (article2.published - article1.published).days + 7
                else: 
                    break
        
            for component in nx.weakly_connected_components(graph):
                latest_dated_article = max(
                    (articles_dict[article_id] for article_id in component),
                    key=lambda x: x.published,
                )

                if latest_dated_article.published > (
                    article1.published + timedelta(days=7)
                ):
                    incident = Incident.objects.create(title=article1.headline)

                    article1.incident = incident
                    article1.save()

                    for article_id in component:
                        articles_dict[article_id].incident = incident
                        articles_dict[article_id].save()
                




        '''
        stories = {}
        sorted_articles = sorted(articles, key=lambda x: x.published)

        for i, article1 in enumerate(sorted_articles):
            window = 7
            stories[i] = []
            stories[i].append(article1)
            for article2 in sorted_articles[i+1:]:

                # Check if the articles are within a 7-day window
                if (article2.published - article1.published).days <= timedelta(days = window):
                    similarity = calculate_tfidf_similarity(article1.body, article2.body)

                    # Check if the similarity is greater than a threshold
                    if similarity >= 0.25:
                        stories[i].append(article2)
                        sorted_articles.pop(article2)
                        window = (article2.published - article1.published).days + 7
                else:
                    break
                    
        '''

        
        
    def calculate_tfidf_similarity(self, text1: str, text2: str):
        # Create a TF-IDF vectorizer
        vectorizer = TfidfVectorizer()

        # Fit and transform the texts into TF-IDF vectors
        tfidf_matrix = vectorizer.fit_transform([text1, text2])

        # Calculate the cosine similarity between the TF-IDF vectors
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # The similarity value is in the upper-right corner of the matrix
        similarity = similarity_matrix[0, 1]

        return similarity
    

'''

        questions = {key: QUESTIONS[key] for key in ["title", "summary"]}

        questions_chat = questions
        
        incidents = list(Incident.objects.prefetch_related('articles'))

        #postmortem_keys = ["summary", "time", "system", "ResponsibleOrg", "ImpactedOrg"]
        #weights = [0.20, 0.20, 0.20, 0.20, 0.20]

        postmortem_keys = ["summary"]
        weights = [1]

        chatGPT = ChatGPT()
        embedder = EmbedderGPT()
        classifierChatGPT = ClassifierChatGPT()
        temp = args.temp if 0 <= args.temp <= 1 else 0
        inputs = {"model": "gpt-3.5-turbo", "temperature": temp}

        logging.info("\n\nMerging Articles.")

        for article_new in queryset:

            logging.info("\nSearching for incident for article: %s.", article_new)

            # Create embeddings for the new article's postmortem information
            article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "summary")

            article_new.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

            similar_found = False #TODO: what happens when = None (ex: due to api error), it could cause article not to merge and create new incident, in this case it should skip the article, initialize with none?
            
            for incident in incidents:
                logging.info("Searching within incident: %s.", incident)
                for article_incident in incident.articles.all():
                    
                    mean_score = 0
                    sum_scores = 0
                    for ind, postmortem_key in enumerate(postmortem_keys):
                        # Calculate similarity between articles based on embeddings
                        incident_similarity = article_new.cosine_similarity(article_incident, postmortem_key + "_embedding") 
                        sum_scores += incident_similarity * weights[ind]
                    
                    mean_score = sum_scores #/len(postmortem_keys)                    

                    if mean_score > 0.85:
                        logging.info("High similarity score of " + str(mean_score) + " in article: " + str(article_incident.headline))

                        #TODO: Measure false positive rate with just cosine similarity


                        #Confirm with LLM
                        content = "You will classify whether two paragraphs descibe the same software failure incident (software failure could mean a " + FAILURE_SYNONYMS + ")"

                        messages = [
                                {"role": "system", 
                                "content": content}
                                ]

                        prompt = "Does the provided paragraph 1 and paragraph 2 describe the same software failure incident(s)?\n" \
                                + "\nParagraph 1: " + article_new.summary \
                                + "\nParagraph 2: " + article_incident.summary \
                                + "\nAnswer with just True or False."

                        messages.append(
                                        {"role": "user", "content": prompt },
                                        )
                        
                        inputs["messages"] = messages
                        similar_found = classifierChatGPT.run(inputs)

                        if similar_found is True:
                            logging.info("Found incident match with a score of " + str(mean_score) + " in incident: " + str(incident))
                            article_new.incident = incident
                            article_new.save()

                            break

                        elif similar_found is None:
                            logging.info("Similar found is None, skipping article for now.")
                            break


                        #similar_found = True
                        #article_new.incident = incident
                        #article_new.save()
                        #break
                
                if similar_found is True or similar_found is None:
                    break

            if similar_found is False:
                article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "title")

                logging.info("Incident match not found, creating new incident: %s.", article_new.title)

                incident = Incident.objects.create(title=article_new.title)

                article_new.incident = incident
                article_new.save()

                incidents.append(incident)

        logging.info("Articles merged!")
'''