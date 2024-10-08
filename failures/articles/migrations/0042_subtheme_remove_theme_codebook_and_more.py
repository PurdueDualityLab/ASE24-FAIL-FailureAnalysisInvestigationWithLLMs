# Generated by Django 4.1.3 on 2024-04-24 17:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0041_theme_parent_theme"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubTheme",
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
                    "postmortem_key",
                    models.CharField(
                        help_text="The postmortem of which the theme belongs.",
                        max_length=100,
                        verbose_name="Postmortem Key",
                    ),
                ),
                (
                    "sub_theme",
                    models.CharField(
                        help_text="The sub theme name.",
                        max_length=100,
                        verbose_name="Sub theme",
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
                    "incidents",
                    models.ManyToManyField(
                        blank=True,
                        related_name="sub_themes",
                        to="articles.incident",
                        verbose_name="Incidents",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="theme",
            name="codebook",
        ),
        migrations.RemoveField(
            model_name="theme",
            name="parent_theme",
        ),
        migrations.AddField(
            model_name="theme",
            name="incidents",
            field=models.ManyToManyField(
                blank=True,
                related_name="themes",
                to="articles.incident",
                verbose_name="Incidents",
            ),
        ),
        migrations.AddField(
            model_name="theme",
            name="postmortem_key",
            field=models.CharField(
                default="no_val",
                help_text="The postmortem of which the theme belongs.",
                max_length=100,
                verbose_name="Postmortem Key",
            ),
        ),
        migrations.AlterField(
            model_name="theme",
            name="definition",
            field=models.TextField(
                default="no_val",
                help_text="The definition of the theme.",
                verbose_name="Definition",
            ),
        ),
        migrations.AlterField(
            model_name="theme",
            name="theme",
            field=models.CharField(
                default="no_val",
                help_text="The theme name.",
                max_length=100,
                verbose_name="Theme",
            ),
        ),
        migrations.DeleteModel(
            name="Codebook",
        ),
        migrations.AddField(
            model_name="subtheme",
            name="theme",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subthemes",
                to="articles.theme",
                verbose_name="Theme",
            ),
        ),
    ]
