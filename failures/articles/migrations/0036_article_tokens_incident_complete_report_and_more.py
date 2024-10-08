# Generated by Django 4.1.3 on 2024-03-21 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0035_article_fixes_article_fixes_embedding_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="tokens",
            field=models.FloatField(
                blank=True,
                help_text="Number of Tokens in article body.",
                null=True,
                verbose_name="Tokens in Body",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="complete_report",
            field=models.BooleanField(
                help_text="Whether the incident report has been completely filled out.",
                null=True,
                verbose_name="Report Complete",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="experiment",
            field=models.BooleanField(
                help_text="Whether the incident is part of the experiment suite.",
                null=True,
                verbose_name="Experiment",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="new_article",
            field=models.BooleanField(
                help_text="Whether the incident has a new article merged in, where the incident report has to be updated.",
                null=True,
                verbose_name="New Article",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="tokens",
            field=models.FloatField(
                blank=True,
                help_text="Number of total Tokens in all articles in incident.",
                null=True,
                verbose_name="Total Tokens in Incident",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="article_summary",
            field=models.TextField(
                blank=True,
                help_text="Summary of the article generated by an OS summarizer model.",
                verbose_name="Article Summary",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="scraped_at",
            field=models.DateTimeField(
                auto_now_add=True,
                help_text="Date and time when the article was scraped.",
                verbose_name="Scraped At",
            ),
        ),
    ]
