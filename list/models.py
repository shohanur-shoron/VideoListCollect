from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class YouTubeVideo(models.Model):
    url = models.URLField(
        help_text="Full YouTube URL (short or long form)."
    )
    image_url = models.URLField(null=True, blank=True)
    video_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Extracted YouTube video ID (unique)."
    )
    channel_name = models.CharField(
        max_length=255,
        help_text="Human-readable channel name."
    )
    title = models.CharField(
        max_length=1000,
        help_text="Video title."
    )
    type = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    duration_seconds = models.PositiveIntegerField(
        help_text="Duration of the video in seconds (e.g., 9000s to 10800s)."
    )
    duration = models.CharField(
        max_length=20,
        help_text="Human-readable duration (e.g. '2h 34m 3s')."
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who submitted the link."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created."
    )


    def save(self, *args, **kwargs):
        """
        Override save() so whenever duration_seconds is set,
        we auto-update the human-readable duration CharField.
        """
        self.duration = self.format_duration(self.duration_seconds)
        super().save(*args, **kwargs)

    @staticmethod
    def format_duration(total_seconds: int) -> str:
        """
        Convert an integer number of seconds into a
        human-readable string: Hh Mm Ss (e.g. "2h 34m 3s").
        Handles hours, minutes, and seconds.
        """
        hours = total_seconds // 3600
        remainder = total_seconds % 3600
        minutes = remainder // 60
        seconds = remainder % 60

        parts = []
        if hours > 0:
            parts.append(f"{int(hours)}h")
        if minutes > 0:
            parts.append(f"{int(minutes)}m")
        if seconds > 0:
            parts.append(f"{int(seconds)}s")

        # If total_seconds = 0 (shouldn't happen if min is 1),
        # or if there's no hours/minutes, we still return something.
        if not parts:
            return "0s"

        return " ".join(parts)
    
    
    def __str__(self):
        return f"{self.title} ({self.video_id})"

