from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from failures.articles.models import Article, Incident, SearchQuery, Article_Ko, Theme, SubTheme, RiskRecord

from import_export.admin import ImportExportModelAdmin


'''
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "headline",
        "title",
        "published",
        "source",
        "describes_failure",
        "summary",
        "system",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "mitigations",
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
    list_filter = ("describes_failure",)

'''

@admin.register(Article_Ko)
class Article_KoAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "incident_id",
        "storyID",
        "articleID",
        "headline",
        "summary",
        "body",
    )
    
    def incident_id(self, obj):
        return obj.incident_id if obj.incident_id else "-"
    
    incident_id.short_description = 'Incident ID'

    search_fields = ["storyID"]

@admin.register(Article)
class ArticleAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "experiment",
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
    
'''
class ArticleInline(admin.TabularInline):
    model = Article

#@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    inlines = [
        ArticleInline,
    ]

admin.site.register(Incident, IncidentAdmin)
'''

@admin.register(Incident)
class IncidentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "complete_report",
        "experiment",
        "new_article",
        "rag",
        "published",
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
        "references",
        "recurring_option",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "consequence_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "recurring_rationale",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "consequence_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
        "article_ids",
        "get_articles",
    )
    search_fields = ["id"]

    
    def article_ids(self, obj):
        # Fetch and return related Article IDs for the current Incident object
        return ', '.join(str(article.id) for article in obj.articles.all())
    article_ids.short_description = 'Source Article IDs'  # Customize column header
    

    
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
    

    

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = (
        "keyword",
        "start_year",
        "start_month",
        "end_year",
        "end_month",
        "sources",
        "created_at",
        "last_searched_at",
    )
    list_filter = ("created_at", "last_searched_at")


@admin.register(Theme)
class ThemeAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "postmortem_key",
        "theme",
        "definition",
    )
    list_filter = ("postmortem_key",)


@admin.register(SubTheme)
class SubThemeAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "postmortem_key",
        "sub_theme",
        "definition",
    )
    list_filter = ("postmortem_key",)

@admin.register(RiskRecord)
class SubThemeAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "url",
    )
    list_filter = ("url",)


'''
@admin.register(Failure)
class FailureAdmin(admin.ModelAdmin):
    list_display = (
        "published",
        "title",
        "summary",
    )
    list_filter = ("title",)
'''