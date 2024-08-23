from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from failures.articles.models import Article, Incident

class ArticlePublicAdmin(PublicModelAdmin):
    list_display = (
        "id",
        "headline",
        "title",
        "scrape_successful",
        "describes_failure",
        "analyzable_failure",
        "published",
        "source",
        "summary",
        #"summary_embedding",
        "system",
        "ResponsibleOrg",
        "ImpactedOrg",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "preventions",
        "fixes",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
    )
    search_fields = ["id"]

class IncidentPublicAdmin(PublicModelAdmin):
    list_display = (
        "id",
        "title",
        "summary",
        #"summary_embedding",
        "system",
        "ResponsibleOrg",
        "ImpactedOrg",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "preventions",
        "fixes",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
        "get_articles",
    )
    search_fields = ["title"]

    '''
    def get_articles(self, obj):
        articles = obj.articles.all()

        return ", ".join([article.headline for article in articles])

    get_articles.short_description = "Source Articles"
    '''

    
    def article_admin_url(self, article_id):
        # Construct the URL to the article change page in the admin
        return reverse("admin:articles_article_change", args=[article_id])

    def get_articles(self, obj):
        articles = obj.articles.all()
        articles_links = [
            format_html('<a href="{}">{}</a>', self.article_admin_url(article.id), article.headline)
            for article in articles
        ]

        return format_html(", ".join(articles_links))
    
    get_articles.short_description = "Source Articles"


public_app = PublicApp("articles", models=("Article", "Incident"))
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Article, ArticlePublicAdmin)
public_admin.register(Incident, IncidentPublicAdmin)