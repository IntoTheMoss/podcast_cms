# Generated by Django 5.1.7 on 2025-03-16 19:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcast", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcastepisodepage",
            name="season_episode_number",
            field=models.IntegerField(
                blank=True,
                help_text="Episode number within the season",
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name="podcastepisodepage",
            name="episode_number",
            field=models.IntegerField(
                help_text="Unique episode number across all seasons",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]
