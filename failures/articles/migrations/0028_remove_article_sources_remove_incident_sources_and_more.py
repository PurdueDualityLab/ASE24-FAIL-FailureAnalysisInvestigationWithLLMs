# Generated by Django 4.1.3 on 2023-11-01 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0027_article_sources_incident_sources"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="article",
            name="sources",
        ),
        migrations.RemoveField(
            model_name="incident",
            name="sources",
        ),
        migrations.AddField(
            model_name="article",
            name="references",
            field=models.TextField(blank=True, null=True, verbose_name="References"),
        ),
        migrations.AddField(
            model_name="incident",
            name="references",
            field=models.TextField(blank=True, null=True, verbose_name="References"),
        ),
    ]