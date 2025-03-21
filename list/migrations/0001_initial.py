# Generated by Django 5.1.4 on 2025-01-13 16:14

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='YouTubeVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(help_text='Full YouTube URL (short or long form).')),
                ('video_id', models.CharField(help_text='Extracted YouTube video ID (unique).', max_length=50, unique=True)),
                ('channel_name', models.CharField(help_text='Human-readable channel name.', max_length=255)),
                ('title', models.CharField(help_text='Video title.', max_length=255)),
                ('duration_seconds', models.PositiveIntegerField(help_text='Duration of the video in seconds (e.g., 9000s to 10800s).', validators=[django.core.validators.MinValueValidator(9000), django.core.validators.MaxValueValidator(10800)])),
                ('duration', models.CharField(help_text="Human-readable duration (e.g. '2h 34m 3s').", max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when this record was created.')),
                ('added_by', models.ForeignKey(blank=True, help_text='User who submitted the link.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
