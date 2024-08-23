# Generated by Django 4.1.3 on 2024-04-22 19:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0039_merge_20240422_1901"),
    ]

    operations = [
        migrations.CreateModel(
            name="Codebook",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "codebook_type",
                    models.CharField(
                        help_text="Type of codebook, e.g., 'SEcauses', 'impacts', etc.",
                        max_length=100,
                        verbose_name="Codebook Type",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Theme",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        help_text="The theme name.",
                        max_length=100,
                        verbose_name="Theme",
                    ),
                ),
                (
                    "definition",
                    models.TextField(
                        help_text="The definition of the theme.",
                        verbose_name="Definition",
                    ),
                ),
                (
                    "codebook",
                    models.ForeignKey(
                        help_text="The codebook associated with this theme.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="themes",
                        to="articles.codebook",
                        verbose_name="Codebook",
                    ),
                ),
            ],
        ),
    ]