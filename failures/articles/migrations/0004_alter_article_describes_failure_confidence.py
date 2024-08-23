# Generated by Django 4.1.3 on 2023-01-05 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0003_article_describes_failure_confidence_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="describes_failure_confidence",
            field=models.FloatField(
                help_text="Confidence of the classifier in whether the article describes a failure.",
                null=True,
                verbose_name="Describes Failure Confidence",
            ),
        ),
    ]