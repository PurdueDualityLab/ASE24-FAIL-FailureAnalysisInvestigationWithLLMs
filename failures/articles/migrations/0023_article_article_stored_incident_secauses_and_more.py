# Generated by Django 4.1.3 on 2023-09-22 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0022_article_analyzable_failure"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="article_stored",
            field=models.BooleanField(
                help_text="Whether the article has been stored into the vector database.",
                null=True,
                verbose_name="Article Stored",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="SEcauses",
            field=models.TextField(
                blank=True, null=True, verbose_name="Software Causes"
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="incident_stored",
            field=models.BooleanField(
                help_text="Whether the incident has been stored into the vector database.",
                null=True,
                verbose_name="Incident Stored",
            ),
        ),
        migrations.AddField(
            model_name="incident",
            name="incident_updated",
            field=models.BooleanField(
                help_text="Whether a new article has been added to the incident.",
                null=True,
                verbose_name="Incident Updated",
            ),
        ),
    ]
