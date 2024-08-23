import datetime
import io
import logging
from typing import Optional


from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

import feedparser
import numpy as np
from newsplease import NewsPlease
from newspaper import Article as NewsScraper
from bs4 import BeautifulSoup
import requests
import re
import json
import sys

from openai.embeddings_utils import cosine_similarity as openai_cosine_similarity

#from failures.commands.PROMPTS import FAILURE_SYNONYMS
FAILURE_SYNONYMS = "hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"



from failures.networks.models import (
    Embedder,
    QuestionAnswerer,
    Summarizer,
    ZeroShotClassifier,
    ChatGPT,
    SummarizerGPT,
    ClassifierChatGPT,
    EmbedderGPT,
)

from failures.parameters.models import Parameter


class SearchQuery(models.Model):
    keyword = models.CharField(
        _("Keyword"),
        max_length=255,
        help_text=_("Keyword to use for searching for news articles."),
    )

    start_year = models.IntegerField(
        _("Start Year"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched from this year onwards. This field is optional."
        ),
    )

    end_year = models.IntegerField(
        _("End Year"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched until this year. This field is optional."
        ),
    )

    start_month = models.IntegerField(
        _("Start Month"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched from this month onwards. This field is optional."
        ),
    )

    end_month = models.IntegerField(
        _("End Month"),
        null=True,
        blank=True,
        help_text=_(
            "News articles will be searched until this month. This field is optional."
        ),
    )

    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("Date and time when this search query was created."),
        editable=False,
    )

    last_searched_at = models.DateTimeField(
        _("Last Searched At"),
        null=True,
        blank=True,
        help_text=_("Date and time when this search query was last searched."),
        editable=False,
    )

    sources = ArrayField(
        models.URLField(max_length=255),
        blank=True,
        null=True,
        verbose_name=_("Sources"),
        help_text=_("Sources to search for news articles, such as nytimes.com,wired.com."),
    )

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")

    def __str__(self):
        return f"{self.keyword}"
    
# TODO: Remove codebook, add sub themes 

class Theme(models.Model):
    incidents = models.ManyToManyField('Incident', related_name='themes', verbose_name=_("Incidents"), blank=True)

    postmortem_key = models.CharField(
        _("Postmortem Key"),
        max_length=100,
        default="no_val",
        help_text=_("The postmortem of which the theme belongs."),
    )
    theme = models.CharField(
        _("Theme"),
        max_length=100,
        default="no_val",
        help_text=_("The theme name."),
    )
    definition = models.TextField(
        _("Definition"),
        default="no_val",
        help_text=_("The definition of the theme."),
    )

    def __str__(self):
        return self.theme
    
class SubTheme(models.Model):  
    postmortem_key = models.CharField(
        _("Postmortem Key"),
        max_length=100,
        default="no_val",
        help_text=_("The postmortem of which the theme belongs."),
    )
    sub_theme = models.CharField(
        _("Sub theme"),
        max_length=100,
        default="no_val",
        help_text=_("The sub theme name."),
    )
    definition = models.TextField(
        _("Definition"),
        default="no_val",
        help_text=_("The definition of the theme."),
    )

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='subthemes', verbose_name=_("Theme"))
    incidents = models.ManyToManyField('Incident', related_name='subthemes', verbose_name=_("Incidents"), blank=True)

    def __str__(self):
        return self.theme

class Incident(models.Model):

    published = models.DateTimeField(_("Published"), help_text=_("Date and time when the earliest article was published."), blank=True, null=True)

    tokens = models.FloatField(
        _("Total Tokens in Incident"), blank=True, null=True, help_text=_("Number of total Tokens in all articles in incident.")
    )

    complete_report = models.BooleanField(
        _("Report Complete"),
        null=True,
        help_text=_(
            "Whether the incident report has been completely filled out."
        ),
    )

    new_article = models.BooleanField(
        _("New Article"),
        null=True,
        help_text=_(
            "Whether the incident has a new article merged in, where the incident report has to be updated."
        ),
    )

    experiment = models.BooleanField(
        _("Experiment"),
        null=True,
        help_text=_(
            "Whether the incident is part of the experiment suite."
        ),
    )

    rag = models.BooleanField(
        _("RAG"),
        null=True,
        help_text=_(
            "Whether RAG was used to create a failure report for the incident."
        ),
    )
    
    #Open ended postmortem fields
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)
    time = models.TextField(_("Time"), blank=True, null=True)
    system = models.TextField(_("System"), blank=True, null=True)
    ResponsibleOrg = models.TextField(_("ResponsibleOrg"), blank=True, null=True)
    ImpactedOrg = models.TextField(_("ImpactedOrg"), blank=True, null=True)
    SEcauses = models.TextField(_("Software Causes"), blank=True, null=True)
    NSEcauses = models.TextField(_("Non-Software Causes"), blank=True, null=True)
    impacts = models.TextField(_("Impacts"), blank=True, null=True)
    preventions = models.TextField(_("Preventions"), blank=True, null=True)
    fixes = models.TextField(_("Fixes"), blank=True, null=True)
    references = models.TextField(_("References"), blank=True, null=True)

    #Taxonomy fields: Options
    recurring_option = models.TextField(_("Recurring Option"), blank=True, null=True)
    phase_option = models.TextField(_("Phase Option"), blank=True, null=True)
    boundary_option = models.TextField(_("Boundary Option"), blank=True, null=True)
    nature_option = models.TextField(_("Nature Option"), blank=True, null=True)
    dimension_option = models.TextField(_("Dimension Option"), blank=True, null=True)
    objective_option = models.TextField(_("Objective Option"), blank=True, null=True)
    intent_option = models.TextField(_("Intent Option"), blank=True, null=True)
    capability_option = models.TextField(_("Capability Option"), blank=True, null=True)
    duration_option = models.TextField(_("Duration Option"), blank=True, null=True)
    behaviour_option = models.TextField(_("Behaviour Option"), blank=True, null=True)
    domain_option = models.TextField(_("Domain Option"), blank=True, null=True)
    consequence_option = models.TextField(_("Consequence Option"), blank=True, null=True)
    cps_option = models.TextField(_("CPS Option"), blank=True, null=True)
    perception_option = models.TextField(_("Perception Option"), blank=True, null=True)
    communication_option = models.TextField(_("Communication Option"), blank=True, null=True)
    application_option = models.TextField(_("Application Option"), blank=True, null=True)
    

    #Taxonomy fields: Explanations
    recurring_rationale = models.TextField(_("Recurring Rationale"), blank=True, null=True)
    phase_rationale = models.TextField(_("Phase Rationale"), blank=True, null=True)
    boundary_rationale = models.TextField(_("Boundary Rationale"), blank=True, null=True)
    nature_rationale = models.TextField(_("Nature Rationale"), blank=True, null=True)
    dimension_rationale = models.TextField(_("Dimension Rationale"), blank=True, null=True)
    objective_rationale = models.TextField(_("Objective Rationale"), blank=True, null=True)
    intent_rationale = models.TextField(_("Intent Rationale"), blank=True, null=True)
    capability_rationale = models.TextField(_("Capability Rationale"), blank=True, null=True)
    duration_rationale = models.TextField(_("Duration Rationale"), blank=True, null=True)
    behaviour_rationale = models.TextField(_("Behaviour Rationale"), blank=True, null=True)
    domain_rationale = models.TextField(_("Domain Rationale"), blank=True, null=True)
    consequence_rationale = models.TextField(_("Consequence Rationale"), blank=True, null=True)
    cps_rationale = models.TextField(_("CPS Rationale"), blank=True, null=True)
    perception_rationale = models.TextField(_("Perception Rationale"), blank=True, null=True)
    communication_rationale = models.TextField(_("Communication Rationale"), blank=True, null=True)
    application_rationale = models.TextField(_("Application Rationale"), blank=True, null=True)

    #Embeddings
    summary_embedding = models.TextField(_("Summary Embedding"), blank=True, null=True)
    time_embedding = models.TextField(_("Time Embedding"), blank=True, null=True)
    system_embedding = models.TextField(_("System Embedding"), blank=True, null=True)
    ResponsibleOrg_embedding = models.TextField(_("ResponsibleOrg Embedding"), blank=True, null=True)
    ImpactedOrg_embedding = models.TextField(_("ImpactedOrg Embedding"), blank=True, null=True)

    SEcauses_embedding = models.TextField(_("Software Causes Embedding"), blank=True, null=True)
    NSEcauses_embedding = models.TextField(_("Non-Software Causes Embedding"), blank=True, null=True)
    impacts_embedding = models.TextField(_("Impacts Embedding"), blank=True, null=True)
    preventions_embedding = models.TextField(_("Preventions Embedding"), blank=True, null=True)
    fixes_embedding = models.TextField(_("Fixes Embedding"), blank=True, null=True)

    '''
    incident_updated = models.BooleanField(
        _("Incident Updated"),
        null=True,
        help_text=_(
            "Whether a new article has been added to the incident."
        ),
    )

    incident_stored = models.BooleanField(
        _("Incident Stored"),
        null=True,
        help_text=_(
            "Whether the incident has been stored into the vector database."
        ),
    )
    '''



    class Meta:
        verbose_name = _("Incident")
        verbose_name_plural = _("Incidents")
        

    def __str__(self):
        return self.title


class Article(models.Model):

    incident = models.ForeignKey(Incident, blank=True, null=True, on_delete=models.SET_NULL, related_name='articles')

    search_queries = models.ManyToManyField(
        SearchQuery,
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Search Queries"),
    )


    # Marking url as unique=True because we don't want to store the same article twice
    url = models.URLField(
        _("URL"), unique=True, max_length=2048, help_text=_("URL of the article.")
    )

    published = models.DateTimeField(
        _("Published"), help_text=_("Date and time when the article was published.")
    )

    source = models.URLField(
        _("Source"),
        help_text=_("URL of the source of the article, such as nytimes.com."),
    )

    article_summary = models.TextField(
        _("Article Summary"),
        blank=True,
        help_text=_("Summary of the article generated by an OS summarizer model."),
    )

    body = models.TextField(
        _("Body"), blank=True, help_text=_("Body of the article scraped from the URL.")
    )

    tokens = models.FloatField(
        _("Tokens in Body"), blank=True, null=True, help_text=_("Number of Tokens in article body.")
    )

    embedding = models.FileField(
        _("Embedding"),
        upload_to="embeddings",
        null=True,
        help_text=_("NumPy array of the embedding of the article stored as a file."),
        editable=False,
    )

    scraped_at = models.DateTimeField(
        _("Scraped At"),
        auto_now_add=True,
        help_text=_("Date and time when the article was scraped."),
        editable=False,
    )

    scrape_successful = models.BooleanField(
        _("Scrape Successful"),
        null=True,
        help_text=_(
            "Whether the article was scraped successfully."
        ),
    )


    describes_failure = models.BooleanField(
        _("Describes Failure"),
        null=True,
        help_text=_(
            "Whether the article describes a failure. This field is set by ChatGPT."
        ),
    )

    analyzable_failure = models.BooleanField(
        _("Analyzable Failure"),
        null=True,
        help_text=_(
            "Whether the article can be used to conduct a failure analysis. This field is set by ChatGPT."
        ),
    )

    article_stored = models.BooleanField(
        _("Article Stored"),
        null=True,
        help_text=_(
            "Whether the article has been stored into the vector database."
        ),
    )

    experiment = models.BooleanField(
        _("Experiment"),
        null=True,
        help_text=_(
            "Whether the article is part of the experiment suite."
        ),
    )


    similarity_score = models.FloatField(_("Cosine similarity score"),null=True,blank=True)
    
    headline = models.TextField(_("Headline"), blank=True, null=True)
    
    #Open ended postmortem fields
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)
    system = models.TextField(_("System"), blank=True, null=True)
    time = models.TextField(_("Time"), blank=True, null=True)
    SEcauses = models.TextField(_("Software Causes"), blank=True, null=True)
    NSEcauses = models.TextField(_("Non-Software Causes"), blank=True, null=True)
    impacts = models.TextField(_("Impacts"), blank=True, null=True)
    preventions = models.TextField(_("Preventions"), blank=True, null=True)
    fixes = models.TextField(_("Fixes"), blank=True, null=True)
    ResponsibleOrg = models.TextField(_("ResponsibleOrg"), blank=True, null=True)
    ImpactedOrg = models.TextField(_("ImpactedOrg"), blank=True, null=True)
    references = models.TextField(_("References"), blank=True, null=True)

    #Taxonomy fields: Options
    phase_option = models.TextField(_("Phase Option"), blank=True, null=True)
    boundary_option = models.TextField(_("Boundary Option"), blank=True, null=True)
    nature_option = models.TextField(_("Nature Option"), blank=True, null=True)
    dimension_option = models.TextField(_("Dimension Option"), blank=True, null=True)
    objective_option = models.TextField(_("Objective Option"), blank=True, null=True)
    intent_option = models.TextField(_("Intent Option"), blank=True, null=True)
    capability_option = models.TextField(_("Capability Option"), blank=True, null=True)
    duration_option = models.TextField(_("Duration Option"), blank=True, null=True)
    domain_option = models.TextField(_("Domain Option"), blank=True, null=True)
    cps_option = models.TextField(_("CPS Option"), blank=True, null=True)
    perception_option = models.TextField(_("Perception Option"), blank=True, null=True)
    communication_option = models.TextField(_("Communication Option"), blank=True, null=True)
    application_option = models.TextField(_("Application Option"), blank=True, null=True)
    behaviour_option = models.TextField(_("Behaviour Option"), blank=True, null=True)
    

    #Taxonomy fields: Explanations
    phase_rationale = models.TextField(_("Phase Rationale"), blank=True, null=True)
    boundary_rationale = models.TextField(_("Boundary Rationale"), blank=True, null=True)
    nature_rationale = models.TextField(_("Nature Rationale"), blank=True, null=True)
    dimension_rationale = models.TextField(_("Dimension Rationale"), blank=True, null=True)
    objective_rationale = models.TextField(_("Objective Rationale"), blank=True, null=True)
    intent_rationale = models.TextField(_("Intent Rationale"), blank=True, null=True)
    capability_rationale = models.TextField(_("Capability Rationale"), blank=True, null=True)
    duration_rationale = models.TextField(_("Duration Rationale"), blank=True, null=True)
    domain_rationale = models.TextField(_("Domain Rationale"), blank=True, null=True)
    cps_rationale = models.TextField(_("CPS Rationale"), blank=True, null=True)
    perception_rationale = models.TextField(_("Perception Rationale"), blank=True, null=True)
    communication_rationale = models.TextField(_("Communication Rationale"), blank=True, null=True)
    application_rationale = models.TextField(_("Application Rationale"), blank=True, null=True)
    behaviour_rationale = models.TextField(_("Behaviour Rationale"), blank=True, null=True)

    #Embeddings
    summary_embedding = models.TextField(_("Summary Embedding"), blank=True, null=True)
    time_embedding = models.TextField(_("Time Embedding"), blank=True, null=True)
    system_embedding = models.TextField(_("System Embedding"), blank=True, null=True)
    ResponsibleOrg_embedding = models.TextField(_("ResponsibleOrg Embedding"), blank=True, null=True)
    ImpactedOrg_embedding = models.TextField(_("ImpactedOrg Embedding"), blank=True, null=True)

    SEcauses_embedding = models.TextField(_("Software Causes Embedding"), blank=True, null=True)
    NSEcauses_embedding = models.TextField(_("Non-Software Causes Embedding"), blank=True, null=True)
    impacts_embedding = models.TextField(_("Impacts Embedding"), blank=True, null=True)
    preventions_embedding = models.TextField(_("Preventions Embedding"), blank=True, null=True)
    fixes_embedding = models.TextField(_("Fixes Embedding"), blank=True, null=True)
    

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.headline #TODO: Check places where you use this: Do you want to get headline or title?

    '''
    def has_manual_annotation(self) -> bool:
        return self.failures.filter(manual_annotation=True).exists()
    '''

    @classmethod
    def create_from_google_news_rss_feed(
        cls,
        search_query: SearchQuery,
    ):
        url = cls.format_google_news_rss_url(
            search_query.keyword,
            search_query.start_year,
            search_query.end_year,
            search_query.start_month,
            search_query.end_month,
            search_query.sources,
        )
        logging.info("RSS url: " + str(url))
        articles = []
        feed = feedparser.parse(url)
        search_query.last_searched_at = datetime.datetime.now()
        search_query.save()
        for entry in feed.entries:
            # TODO: reduce queries here
            # Continue if "opinion" in title
            if "opinion" in entry["title"].lower():
                continue
            try:
                dest_url = requests.get(entry.link) 
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to get link: %s: %s.", entry.link, e)
                continue
            dest_url = dest_url.url
            if not cls.objects.filter(url=dest_url).exists():
                article = cls.objects.create(
                    headline=entry["title"],
                    url=dest_url,
                    # example: Mon, 24 Oct 2022 11:00:00 GMT
                    published=datetime.datetime.strptime(
                        entry["published"], "%a, %d %b %Y %H:%M:%S %Z"
                    ),
                    source=entry["source"]["href"],
                )
                logging.info("Created article: %s.", article)
            else:
                article = cls.objects.get(url=dest_url)
            logging.info(
                f"Adding search query to article: %s - %s.", article, search_query
            )
            article.search_queries.add(search_query)
            article.save()
            articles.append(article)
        return articles

    # TODO: should this method be on SearchQuery?
    @staticmethod
    def format_google_news_rss_url(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ) -> str:
        keyword = keyword.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={keyword}"
        if start_year:
            url += f"%20after%3A{start_year}-{start_month}-01"
        if end_year:
            url += f"%20before%3A{end_year}-{end_month}-01" #TODO: Remove 15
        for i, source in enumerate(sources):
            if i > 0:
                url += "%20OR"
            url += f"%20site%3Ahttps%3A%2F%2F{source}"
        url += "&hl=en-US&gl=US&ceid=US%3Aen"

        return url

    #TODO: Cleanup
    '''
    def scrape_body(self):
        try:
            article = NewsPlease.from_url(self.url)
        except Exception as e:
            logging.error(f"Failed to scrape article %s: %s.", self, e)
            return
        if article.maintext is None:
            logging.error("Failed to scrape article %s: No text found.", self)
            return
        self.body = article.maintext
        self.save()
        logging.info(f"Scraped body for %s.", self)
        return self.body
    '''
    def scrape_body(self):
        try:
            #dest_url = requests.get(self.url) #TODO: Need to move this earlier, because this is how we check if an article already exists
            #self.url = dest_url.url
            article_scrape = NewsScraper(self.url)
            article_scrape.download()
            article_scrape.parse()
            article_text = self.preprocess_html(article_scrape)
        except Exception as e:
            logging.error(f"Failed to scrape article %s: %s.", self, e)
            self.scrape_successful = False
            return
        if article_text is None or article_text == "":
            logging.error("Failed to scrape article %s: No text found.", self)
            self.scrape_successful = False
            return
        self.body = article_text
        self.save()
        logging.info(f"Scraped body for %s.", self)
        return self.body
    
    def preprocess_html(self, article_scrape):
        logging.info(f"Processing html for %s.", self)

        article_text = None

        #Scrape text from WIRED
        if "wired" in article_scrape.url:
            html_string = article_scrape.html
            soup = BeautifulSoup(html_string, 'html.parser')
            article_div = soup.find_all("div", attrs={"class": "body__inner-container"})
            article_text = ""
            for text in article_div:
                article_text = article_text + " " + text.get_text(separator=' ')

        #Scrape text from NYT
        elif "nytimes" in article_scrape.url:
            html_string = article_scrape.html
            soup = BeautifulSoup(html_string, 'html.parser')
            article_div = soup.find_all("section", attrs={"name": "articleBody"})
            article_text = ""
            for text in article_div:
                article_text = article_text + " " + text.get_text(separator=' ')

        else:
            #logging.info("URL is not NYT or WIRED: " + article_scrape.url + " for article: " + str(self))
            article_text = article_scrape.text
        
        if article_text is None or len(article_text.split()) < 100:
            logging.info("Issue parsing: " + article_scrape.url + " for article: " + str(self))
            self.scrape_successful = False
            article_text = article_scrape.text
        else:
            self.scrape_successful = True

        article_text = "Published on " + str(article_scrape.published_date) + ". " + article_text #TODO: Error: Fixed from "publish" to "published" on 1/24/24

        self.save()

        return article_text

    def summarize_body(self, summarizer: Summarizer):
        self.article_summary: str = summarizer.run(self.body)
        self.save()
        return self.article_summary

    '''
    def create_embedding(self, embedder: Embedder):
        embedding = embedder.run(self.body)
        bytes_io = io.BytesIO()
        numpy.save(bytes_io, embedding)
        self.embedding.save("embedding.npy", bytes_io)
        self.save()
        return self.embedding
    '''

    def create_postmortem_embeddings_GPT(self, embedder: EmbedderGPT, postmortem_keys: list, query_all: bool): #TODO: Remove? No longer clustering by articles which is what this was used for

        for postmortem_key in postmortem_keys:
            answer_set = True

            postmortem_embedding_key = postmortem_key + "_embedding"
            if not getattr(self, postmortem_embedding_key):
                answer_set = False
            
            if query_all or not answer_set: 

                logging.info("Getting embedding for: " + postmortem_embedding_key)
                
                embeddings = embedder.run(getattr(self, postmortem_key))

                setattr(self, postmortem_embedding_key, json.dumps(embeddings))
            
        self.save()


    def cosine_similarity(self, other: "Article", option_key) -> float:
        if not getattr(self, option_key) or not getattr(self, option_key):
            raise ValueError("One or both articles have no " + option_key)
        
        embedding_self = json.loads(getattr(self, option_key))
        embedding_other = json.loads(getattr(other, option_key))

        similarity_score = openai_cosine_similarity(embedding_self, embedding_other)

        if "summary" in option_key:
            self.similarity_score = similarity_score
        return similarity_score
    
        #return np.dot(embedding_self, embedding_other) / (np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two))

    #Open source classifier
    def classify_as_failure_os(self, classifier: ZeroShotClassifier, labels: list[str]):
        classify_data = {"text": self.body, "labels": labels}
        prediction: tuple[str, float] = classifier.run(classify_data)
        self.describes_failure_os = classifier.labels.index(prediction[0]) == 0
        self.describes_failure_confidence = prediction[1]

        self.save()
        return self.describes_failure_os

    # GPT based classifier for reports on software failure
    def classify_as_failure_ChatGPT(self, classifier: ClassifierChatGPT, inputs: dict):
        
        article_text = self.body

        content = "You will help classify whether an article reports on a software failure incident."

        messages = [
                {"role": "system", 
                "content": content}
                ]

        prompt = "Does the provided article report on a software failure incident(s) (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "\n" \
                + "Answer with just True or False." \
                + "\n" \
                + "Article: " + article_text
        
        messages.append(
                        {"role": "user", "content": prompt },
                        )
        
        inputs["messages"] = messages
        
        self.describes_failure = classifier.run(inputs)

        self.save()
        return self.describes_failure


    # GPT based classifier for: Does the article have enough information to conduct failure analysis
    def classify_as_analyzable_ChatGPT(self, classifier: ClassifierChatGPT, inputs: dict):

        #Truncate article if it is too long
        #article_text = self.body.split()[:2750]
        #article_text = ' '.join(article_text)
        
        article_text = self.body

        content = "You will help classify whether an article contains information to conduct failure analysis about a software failure."

        messages = [
                {"role": "system", 
                "content": content}
                ]

        ''' Prompt version 1:
        prompt = "Does the provided article contain enough information about the provided criteria to conduct a failure analysis of the software failure incident(s) (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "Answer with just True or False." \
                + "\n" \
                + "Criteria: System that failed, cause of failure, and impact of failure." \
                + "\n" \
                + "Article: " + article_text
        ''' 
        #Prompt version 2:
        prompt = "Does the provided article contain information about the provided criteria about the software failure (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "Answer with just True or False." \
                + "\n" \
                + "Criteria: System that failed, cause of failure, and impact of failure." \
                + "\n" \
                + "Article: " + article_text


        messages.append(
                        {"role": "user", "content": prompt },
                        )
        
        inputs["messages"] = messages
        
        self.analyzable_failure = classifier.run(inputs)

        self.save()
        return self.analyzable_failure


    def postmortem_from_article_ChatGPT( #OUTDATED
        self,
        ChatGPT: ChatGPT,
        inputs: dict,
        questions: dict,
        taxonomy_options: dict,
        query_all: bool,
        query_key: str,
    ): 

        logging.info("Extracting postmortem from article: %s.", self)

        
        article_body = self.body
        
        #Pre-process articles if they are too long
        article_len = len(article_body.split())
        if article_len > 2750:
            article_begin = article_body.split()[:-(article_len-2500)]
            article_end = article_body.split()[-(article_len-2500):]
                
            if len(article_end) > 2750: #if the last part of article is too long, just truncate it
                article_end = article_end[:2500]

            content = "You will summarize a part of an article."
            messages = [
                    {"role": "system", 
                    "content": content}
                    ]
            messages.append(
                            {"role": "user", "content": "summarize this text (retain information relevant to software failure) with a maximum of 500 words: " + ' '.join(article_end)},
                            )
            
            inputs["messages"] = messages
            reply = ChatGPT.run(inputs)

            article_body = ' '.join(article_begin) + reply
            logging.info("Reduced articled length for article: "+ str(self) + "; Old length: " + str(article_len) + " ; New length: " + str(len(article_body.split())) )


        #Create postmortems
        content = "You will answer questions about a software failure using information from on an article."

        
        if query_key in questions.keys():
            question_keys = [query_key]
        else:
            question_keys = list(questions.keys())

        #logging.info(question_keys)

        postmortem = {}
        for question_key in question_keys: #[list(questions.keys())[i] for i in [0,2,4,8,16,21]]: #list(questions.keys()):

            #logging.info(question_key)
            
            #Check if the question has already been answered
            answer_set = True
            if question_key in taxonomy_options.keys():
                question_option_key = question_key + "_option"
                question_rationale_key = question_key + "_rationale"
                if not getattr(self, question_option_key):
                    answer_set = False
            else:
                if not getattr(self, question_key):
                    answer_set = False

            if query_all or (query_key in question_key) or not answer_set: 

                logging.info("Querying question: " + str(question_key))

                messages = [
                        {"role": "system", 
                        "content": content}
                        ]

                failure_synonyms = FAILURE_SYNONYMS
                
                prompt = "Answer the provided question using information from the provided article. Note that software failure could mean a " + failure_synonyms + "." \
                        + "\n" \
                        + "Question: " + questions[question_key] \
                        + "\n" \
                        + "Article: " + article_body


                messages.append(
                                {"role": "user", "content": prompt},
                                )
                
                inputs["messages"] = messages

                reply = ChatGPT.run(inputs)

                if "{" and "}" in reply:
                    try:
                        #logging.info("Found json")

                        # extract the values for "explanation" and "option" using capturing groups
                        match = re.search(r'{"explanation": "(.*)", "option": (.*)}', reply)
                        # sanitize the values if there're quotes
                        explanation = match.group(1).replace('"', '\\"')
                        option = match.group(2).replace('"', '')
                        try:
                            #logging.info("Trying to catch option")
                            if "-1" in option:
                                option_value = taxonomy_options[question_key]["-1"]
                            else:
                                option_value = taxonomy_options[question_key][option]
                        except:
                            logging.info("Option error")
                            option_value = option

                        reply = {"explanation": explanation,
                                    "option": option_value.lower()
                                    }
                        
                        #if response json is in incorrect format
                    except:
                        logging.info("Incorrect json form")
                        #logging.info(type(reply))
                        reply = reply
                else:

                    reply = reply

                if question_key in taxonomy_options.keys():
                    setattr(self, question_option_key, reply['option'])
                    setattr(self, question_rationale_key, reply['explanation'])
                else:
                    setattr(self, question_key, reply)

        self.save()

        return True

class Incident_Ko(models.Model):

    published = models.DateTimeField(_("Published"), help_text=_("Date and time when the earliest article was published."), blank=True, null=True)
    #TODO: Find the earliest published date and use the month and year
    
    #Open ended postmortem fields
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)
    system = models.TextField(_("System"), blank=True, null=True)
    time = models.TextField(_("Time"), blank=True, null=True)
    SEcauses = models.TextField(_("Software Causes"), blank=True, null=True)
    NSEcauses = models.TextField(_("Non-Software Causes"), blank=True, null=True)
    impacts = models.TextField(_("Impacts"), blank=True, null=True)
    ResponsibleOrg = models.TextField(_("ResponsibleOrg"), blank=True, null=True)
    ImpactedOrg = models.TextField(_("ImpactedOrg"), blank=True, null=True)
    references = models.TextField(_("References"), blank=True, null=True)

    #Taxonomy fields: Options
    phase_option = models.TextField(_("Phase Option"), blank=True, null=True)
    boundary_option = models.TextField(_("Boundary Option"), blank=True, null=True)
    nature_option = models.TextField(_("Nature Option"), blank=True, null=True)
    dimension_option = models.TextField(_("Dimension Option"), blank=True, null=True)
    objective_option = models.TextField(_("Objective Option"), blank=True, null=True)
    intent_option = models.TextField(_("Intent Option"), blank=True, null=True)
    capability_option = models.TextField(_("Capability Option"), blank=True, null=True)
    duration_option = models.TextField(_("Duration Option"), blank=True, null=True)
    domain_option = models.TextField(_("Domain Option"), blank=True, null=True)
    cps_option = models.TextField(_("CPS Option"), blank=True, null=True)
    perception_option = models.TextField(_("Perception Option"), blank=True, null=True)
    communication_option = models.TextField(_("Communication Option"), blank=True, null=True)
    application_option = models.TextField(_("Application Option"), blank=True, null=True)
    behaviour_option = models.TextField(_("Behaviour Option"), blank=True, null=True)
    

    #Taxonomy fields: Explanations
    phase_rationale = models.TextField(_("Phase Rationale"), blank=True, null=True)
    boundary_rationale = models.TextField(_("Boundary Rationale"), blank=True, null=True)
    nature_rationale = models.TextField(_("Nature Rationale"), blank=True, null=True)
    dimension_rationale = models.TextField(_("Dimension Rationale"), blank=True, null=True)
    objective_rationale = models.TextField(_("Objective Rationale"), blank=True, null=True)
    intent_rationale = models.TextField(_("Intent Rationale"), blank=True, null=True)
    capability_rationale = models.TextField(_("Capability Rationale"), blank=True, null=True)
    duration_rationale = models.TextField(_("Duration Rationale"), blank=True, null=True)
    domain_rationale = models.TextField(_("Domain Rationale"), blank=True, null=True)
    cps_rationale = models.TextField(_("CPS Rationale"), blank=True, null=True)
    perception_rationale = models.TextField(_("Perception Rationale"), blank=True, null=True)
    communication_rationale = models.TextField(_("Communication Rationale"), blank=True, null=True)
    application_rationale = models.TextField(_("Application Rationale"), blank=True, null=True)
    behaviour_rationale = models.TextField(_("Behaviour Rationale"), blank=True, null=True)

    #Embeddings
    summary_embedding = models.TextField(_("Summary Embedding"), blank=True, null=True)
    time_embedding = models.TextField(_("Time Embedding"), blank=True, null=True)
    system_embedding = models.TextField(_("System Embedding"), blank=True, null=True)
    ResponsibleOrg_embedding = models.TextField(_("ResponsibleOrg Embedding"), blank=True, null=True)
    ImpactedOrg_embedding = models.TextField(_("ImpactedOrg Embedding"), blank=True, null=True)

    SEcauses_embedding = models.TextField(_("Software Causes Embedding"), blank=True, null=True)
    NSEcauses_embedding = models.TextField(_("Non-Software Causes Embedding"), blank=True, null=True)
    impacts_embedding = models.TextField(_("Impacts Embedding"), blank=True, null=True)

    '''
    incident_updated = models.BooleanField(
        _("Incident_Ko Updated"),
        null=True,
        help_text=_(
            "Whether a new article has been added to the incident."
        ),
    )

    incident_stored = models.BooleanField(
        _("Incident_Ko Stored"),
        null=True,
        help_text=_(
            "Whether the incident has been stored into the vector database."
        ),
    )
    '''



    class Meta:
        verbose_name = _("Incident_Ko")
        verbose_name_plural = _("Incidents_Ko")
        

    def __str__(self):
        return self.title

class Article_Ko(models.Model):

    incident = models.ForeignKey(Incident_Ko, blank=True, null=True, on_delete=models.SET_NULL, related_name='articles')

    storyID = models.IntegerField(
        _("story id"),
        null=True, 
        blank=True,
        help_text=_("Story ID of the Ko article")
    )
    
    articleID = models.IntegerField(
        _("article id"),
        null=True, 
        blank=True,
        help_text=_("Article ID of the Ko article")
    )

    published = models.DateTimeField(
        _("Published"), help_text=_("Date and time when the article was published.")
    )

    source = models.URLField(
        _("Source"),
        help_text=_("URL of the source of the article, such as nytimes.com."),
    )

    article_summary = models.TextField(
        _("article_summary"),
        blank=True,
        help_text=_("Summary of the article generated by an OS summarizer model."),
    )

    body = models.TextField(
        _("Body"), blank=True, help_text=_("Body of the article scraped from the URL.")
    )

    embedding = models.FileField(
        _("Embedding"),
        upload_to="embeddings",
        null=True,
        help_text=_("NumPy array of the embedding of the article stored as a file."),
        editable=False,
    )

    scraped_at = models.DateTimeField(
        _("Scraped at"),
        auto_now_add=True,
        help_text=_("Date and time when the article was scraped."),
        editable=False,
    )

    scrape_successful = models.BooleanField(
        _("Scrape Successful"),
        null=True,
        help_text=_(
            "Whether the article was scraped successfully."
        ),
    )

    relevant_to_story = models.BooleanField(
        _("Relevant to story"),
        null=True,
        help_text=_(
            "Whether the article is relevant to the ko database story."
        ),
    )

    describes_failure = models.BooleanField(
        _("Describes Failure"),
        null=True,
        help_text=_(
            "Whether the article describes a failure. This field is set by ChatGPT."
        ),
    )

    analyzable_failure = models.BooleanField(
        _("Analyzable Failure"),
        null=True,
        help_text=_(
            "Whether the article can be used to conduct a failure analysis. This field is set by ChatGPT."
        ),
    )

    article_stored = models.BooleanField(
        _("Article_Ko Stored"),
        null=True,
        help_text=_(
            "Whether the article has been stored into the vector database."
        ),
    )


    similarity_score = models.FloatField(_("Cosine similarity score"),null=True,blank=True)
    
    headline = models.TextField(_("Headline"), blank=True, null=True)
    
    #Open ended postmortem fields
    title = models.TextField(_("Title"), blank=True, null=True)
    summary = models.TextField(_("Summary"), blank=True, null=True)
    system = models.TextField(_("System"), blank=True, null=True)
    time = models.TextField(_("Time"), blank=True, null=True)
    SEcauses = models.TextField(_("Software Causes"), blank=True, null=True)
    NSEcauses = models.TextField(_("Non-Software Causes"), blank=True, null=True)
    impacts = models.TextField(_("Impacts"), blank=True, null=True)
    ResponsibleOrg = models.TextField(_("ResponsibleOrg"), blank=True, null=True)
    ImpactedOrg = models.TextField(_("ImpactedOrg"), blank=True, null=True)
    references = models.TextField(_("References"), blank=True, null=True)

    #Taxonomy fields: Options
    phase_option = models.TextField(_("Phase Option"), blank=True, null=True)
    boundary_option = models.TextField(_("Boundary Option"), blank=True, null=True)
    nature_option = models.TextField(_("Nature Option"), blank=True, null=True)
    dimension_option = models.TextField(_("Dimension Option"), blank=True, null=True)
    objective_option = models.TextField(_("Objective Option"), blank=True, null=True)
    intent_option = models.TextField(_("Intent Option"), blank=True, null=True)
    capability_option = models.TextField(_("Capability Option"), blank=True, null=True)
    duration_option = models.TextField(_("Duration Option"), blank=True, null=True)
    domain_option = models.TextField(_("Domain Option"), blank=True, null=True)
    cps_option = models.TextField(_("CPS Option"), blank=True, null=True)
    perception_option = models.TextField(_("Perception Option"), blank=True, null=True)
    communication_option = models.TextField(_("Communication Option"), blank=True, null=True)
    application_option = models.TextField(_("Application Option"), blank=True, null=True)
    behaviour_option = models.TextField(_("Behaviour Option"), blank=True, null=True)
    

    #Taxonomy fields: Explanations
    phase_rationale = models.TextField(_("Phase Rationale"), blank=True, null=True)
    boundary_rationale = models.TextField(_("Boundary Rationale"), blank=True, null=True)
    nature_rationale = models.TextField(_("Nature Rationale"), blank=True, null=True)
    dimension_rationale = models.TextField(_("Dimension Rationale"), blank=True, null=True)
    objective_rationale = models.TextField(_("Objective Rationale"), blank=True, null=True)
    intent_rationale = models.TextField(_("Intent Rationale"), blank=True, null=True)
    capability_rationale = models.TextField(_("Capability Rationale"), blank=True, null=True)
    duration_rationale = models.TextField(_("Duration Rationale"), blank=True, null=True)
    domain_rationale = models.TextField(_("Domain Rationale"), blank=True, null=True)
    cps_rationale = models.TextField(_("CPS Rationale"), blank=True, null=True)
    perception_rationale = models.TextField(_("Perception Rationale"), blank=True, null=True)
    communication_rationale = models.TextField(_("Communication Rationale"), blank=True, null=True)
    application_rationale = models.TextField(_("Application Rationale"), blank=True, null=True)
    behaviour_rationale = models.TextField(_("Behaviour Rationale"), blank=True, null=True)

    #Embeddings
    summary_embedding = models.TextField(_("Summary Embedding"), blank=True, null=True)
    time_embedding = models.TextField(_("Time Embedding"), blank=True, null=True)
    system_embedding = models.TextField(_("System Embedding"), blank=True, null=True)
    ResponsibleOrg_embedding = models.TextField(_("ResponsibleOrg Embedding"), blank=True, null=True)
    ImpactedOrg_embedding = models.TextField(_("ImpactedOrg Embedding"), blank=True, null=True)

    SEcauses_embedding = models.TextField(_("Software Causes Embedding"), blank=True, null=True)
    NSEcauses_embedding = models.TextField(_("Non-Software Causes Embedding"), blank=True, null=True)
    impacts_embedding = models.TextField(_("Impacts Embedding"), blank=True, null=True)

    class Meta:
        verbose_name = _("Article_Ko")
        verbose_name_plural = _("Articles_Ko")

    def __str__(self):
        return self.headline #TODO: Check places where you use this: Do you want to get headline or title?

    def summarize_body(self, summarizer: Summarizer):
        self.article_summary: str = summarizer.run(self.body)
        self.save()
        return self.article_summary

    def create_postmortem_embeddings_GPT(self, embedder: EmbedderGPT, postmortem_keys: list, query_all: bool): #TODO: Remove? No longer clustering by articles which is what this was used for

        for postmortem_key in postmortem_keys:
            answer_set = True

            postmortem_embedding_key = postmortem_key + "_embedding"
            if not getattr(self, postmortem_embedding_key):
                answer_set = False
            
            if query_all or not answer_set: 

                logging.info("Getting embedding for: " + postmortem_embedding_key)
                
                embeddings = embedder.run(getattr(self, postmortem_key))

                setattr(self, postmortem_embedding_key, json.dumps(embeddings))
            
        self.save()


    def cosine_similarity(self, other: "Article_Ko", option_key) -> float:
        if not getattr(self, option_key) or not getattr(self, option_key):
            raise ValueError("One or both articles have no " + option_key)
        
        embedding_self = json.loads(getattr(self, option_key))
        embedding_other = json.loads(getattr(other, option_key))

        similarity_score = openai_cosine_similarity(embedding_self, embedding_other)

        if "summary" in option_key:
            self.similarity_score = similarity_score
        return similarity_score
    
        #return np.dot(embedding_self, embedding_other) / (np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two))

    #Open source classifier
    def classify_as_failure_os(self, classifier: ZeroShotClassifier, labels: list[str]):
        classify_data = {"text": self.body, "labels": labels}
        prediction: tuple[str, float] = classifier.run(classify_data)
        self.describes_failure_os = classifier.labels.index(prediction[0]) == 0
        self.describes_failure_confidence = prediction[1]

        self.save()
        return self.describes_failure_os

    # GPT based classifier for reports on software failure #TODO: classify_as_failure_ChatGPT should be a function disjoint from the model, so that we can call it on any body of text.
    def classify_as_failure_ChatGPT(self, classifier: ClassifierChatGPT, inputs: dict):

        #Truncate article if it is too long
        #article_text = self.body.split()[:2750]
        #article_text = ' '.join(article_text)
        
        article_text = self.body

        content = "You will help classify whether an article reports on a software failure."

        messages = [
                {"role": "system", 
                "content": content}
                ]

        prompt = "Does the provided article report on a software failure (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "\n" \
                + "Answer with just True or False." \
                + "\n" \
                + "Article_Ko: " + article_text
        
        #logging.info("\n")
        #logging.info(prompt)

        messages.append(
                        {"role": "user", "content": prompt },
                        )
        
        inputs["messages"] = messages
        
        self.describes_failure = classifier.run(inputs)

        self.save()
        return self.describes_failure


    # GPT based classifier for: Does the article have enough information to conduct failure analysis
    def classify_as_analyzable_ChatGPT(self, classifier: ClassifierChatGPT, inputs: dict):

        #Truncate article if it is too long
        #article_text = self.body.split()[:2750]
        #article_text = ' '.join(article_text)
        
        article_text = self.body

        content = "You will help classify whether an article contains information to conduct failure analysis about a software failure."

        messages = [
                {"role": "system", 
                "content": content}
                ]

        ''' Prompt version 1:
        prompt = "Does the provided article contain enough information about the provided criteria to conduct a failure analysis of the software failure incident(s) (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "Answer with just True or False." \
                + "\n" \
                + "Criteria: System that failed, cause of failure, and impact of failure." \
                + "\n" \
                + "Article_Ko: " + article_text
        ''' 
        #Prompt version 2:
        prompt = "Does the provided article contain information about the provided criteria about the software failure (software failure could mean a " + FAILURE_SYNONYMS + ")?" \
                + "Answer with just True or False." \
                + "\n" \
                + "Criteria: System that failed, cause of failure, and impact of failure." \
                + "\n" \
                + "Article_Ko: " + article_text


        messages.append(
                        {"role": "user", "content": prompt },
                        )
        
        inputs["messages"] = messages
        
        self.analyzable_failure = classifier.run(inputs)

        self.save()
        return self.analyzable_failure


    def postmortem_from_article_ChatGPT( #OUTDATED
        self,
        ChatGPT: ChatGPT,
        inputs: dict,
        questions: dict,
        taxonomy_options: dict,
        query_all: bool,
        query_key: str,
    ): 

        logging.info("Extracting postmortem from article: %s.", self)

        
        article_body = self.body
        
        #Pre-process articles if they are too long
        article_len = len(article_body.split())
        if article_len > 2750:
            article_begin = article_body.split()[:-(article_len-2500)]
            article_end = article_body.split()[-(article_len-2500):]
                
            if len(article_end) > 2750: #if the last part of article is too long, just truncate it
                article_end = article_end[:2500]

            content = "You will summarize a part of an article."
            messages = [
                    {"role": "system", 
                    "content": content}
                    ]
            messages.append(
                            {"role": "user", "content": "summarize this text (retain information relevant to software failure) with a maximum of 500 words: " + ' '.join(article_end)},
                            )
            
            inputs["messages"] = messages
            reply = ChatGPT.run(inputs)

            article_body = ' '.join(article_begin) + reply
            logging.info("Reduced articled length for article: "+ str(self) + "; Old length: " + str(article_len) + " ; New length: " + str(len(article_body.split())) )


        #Create postmortems
        content = "You will answer questions about a software failure using information from on an article."

        
        if query_key in questions.keys():
            question_keys = [query_key]
        else:
            question_keys = list(questions.keys())

        #logging.info(question_keys)

        postmortem = {}
        for question_key in question_keys: #[list(questions.keys())[i] for i in [0,2,4,8,16,21]]: #list(questions.keys()):

            #logging.info(question_key)
            
            #Check if the question has already been answered
            answer_set = True
            if question_key in taxonomy_options.keys():
                question_option_key = question_key + "_option"
                question_rationale_key = question_key + "_rationale"
                if not getattr(self, question_option_key):
                    answer_set = False
            else:
                if not getattr(self, question_key):
                    answer_set = False

            if query_all or (query_key in question_key) or not answer_set: 

                logging.info("Querying question: " + str(question_key))

                messages = [
                        {"role": "system", 
                        "content": content}
                        ]

                failure_synonyms = FAILURE_SYNONYMS
                
                prompt = "Answer the provided question using information from the provided article. Note that software failure could mean a " + failure_synonyms + "." \
                        + "\n" \
                        + "Question: " + questions[question_key] \
                        + "\n" \
                        + "Article_Ko: " + article_body


                messages.append(
                                {"role": "user", "content": prompt},
                                )
                
                inputs["messages"] = messages

                reply = ChatGPT.run(inputs)

                if "{" and "}" in reply:
                    try:
                        #logging.info("Found json")

                        # extract the values for "explanation" and "option" using capturing groups
                        match = re.search(r'{"explanation": "(.*)", "option": (.*)}', reply)
                        # sanitize the values if there're quotes
                        explanation = match.group(1).replace('"', '\\"')
                        option = match.group(2).replace('"', '')
                        try:
                            #logging.info("Trying to catch option")
                            if "-1" in option:
                                option_value = taxonomy_options[question_key]["-1"]
                            else:
                                option_value = taxonomy_options[question_key][option]
                        except:
                            logging.info("Option error")
                            option_value = option

                        reply = {"explanation": explanation,
                                    "option": option_value.lower()
                                    }
                        
                        #if response json is in incorrect format
                    except:
                        logging.info("Incorrect json form")
                        #logging.info(type(reply))
                        reply = reply
                else:

                    reply = reply

                if question_key in taxonomy_options.keys():
                    setattr(self, question_option_key, reply['option'])
                    setattr(self, question_rationale_key, reply['explanation'])
                else:
                    setattr(self, question_key, reply)

        self.save()

        return True


class RiskRecord(models.Model):

    incident = models.ForeignKey(Incident, blank=True, null=True, on_delete=models.SET_NULL, related_name='risks_records')

    # Marking url as unique=True because we don't want to store the same article twice
    url = models.URLField(
        _("URL"), unique=True, max_length=510, help_text=_("URL of the article.")
    )

    published = models.DateTimeField(
        _("Published"), help_text=_("Date and time when the article was published.")
    )

    source = models.URLField(
        _("Source"),
        help_text=_("URL of the source of the article, such as nytimes.com."),
    )

    article_summary = models.TextField(
        _("article_summary"),
        blank=True,
        help_text=_("Summary of the article generated by an OS summarizer model."),
    )

    body = models.TextField(
        _("Body"), blank=True, help_text=_("Body of the article scraped from the URL.")
    )

    embedding = models.FileField(
        _("Embedding"),
        upload_to="embeddings",
        null=True,
        help_text=_("NumPy array of the embedding of the article stored as a file."),
        editable=False,
    )

    scraped_at = models.DateTimeField(
        _("Scraped at"),
        auto_now_add=True,
        help_text=_("Date and time when the article was scraped."),
        editable=False,
    )

    scrape_successful = models.BooleanField(
        _("Scrape Successful"),
        null=True,
        help_text=_(
            "Whether the article was scraped successfully."
        ),
    )

    describes_failure = models.BooleanField(
        _("Describes Failure"),
        null=True,
        help_text=_(
            "Whether the article describes a failure. This field is set by ChatGPT."
        ),
    )

    analyzable_failure = models.BooleanField(
        _("Analyzable Failure"),
        null=True,
        help_text=_(
            "Whether the article can be used to conduct a failure analysis. This field is set by ChatGPT."
        ),
    )

    article_stored = models.BooleanField(
        _("Article Stored"),
        null=True,
        help_text=_(
            "Whether the article has been stored into the vector database."
        ),
    )


    similarity_score = models.FloatField(_("Cosine similarity score"),null=True,blank=True)
    
    headline = models.TextField(_("Headline"), blank=True, null=True)


'''
class FailureCause(models.Model): #TODO: Not used 
    failure = models.ForeignKey(
        "Failure",
        related_name="failure_causes",
        related_query_name="failure_cause",
        on_delete=models.CASCADE,
        verbose_name=_("Failure"),
    )

    description = models.TextField(_("Description"))

    class Meta:
        verbose_name = _("Failure Cause")
        verbose_name_plural = _("Failure Causes")

    def __str__(self):
        return self.description
'''



