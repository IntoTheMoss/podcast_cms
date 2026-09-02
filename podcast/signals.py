"""Keep each episode's MP3 tags in step with the CMS record.

Hooked to `page_published` rather than `save()` on purpose: audio is usually
uploaded before the season, date and artwork are filled in, so publish is the
first moment the record is actually complete.

Re-tagging on *every* publish is also deliberate. It is idempotent, costs a
couple of hundred milliseconds, and quietly repairs episodes whose metadata
was corrected after first release — which is exactly how the season 17
numbering fix reached the files.
"""

import logging

from django.conf import settings
from django.dispatch import receiver
from wagtail.signals import page_published

from .id3 import TaggingError, write_tags
from .models import PodcastEpisodePage

logger = logging.getLogger(__name__)


@receiver(page_published, sender=PodcastEpisodePage)
def write_id3_on_publish(sender, instance, **kwargs):
    """Write the episode's metadata into its MP3 whenever it is published.

    Tagging must never block publishing: a missing file or an unwritable
    directory is worth a log line, not a failed editorial action.
    """
    if not getattr(settings, "PODCAST_WRITE_ID3_ON_PUBLISH", True):
        return

    try:
        note = write_tags(instance)
    except TaggingError as exc:
        logger.warning(
            "ID3 tagging skipped for episode %s: %s", instance.episode_number, exc
        )
    except Exception:  # noqa: BLE001 - never let this break a publish
        logger.exception(
            "Unexpected error writing ID3 tags for episode %s",
            instance.episode_number,
        )
    else:
        logger.info("Wrote ID3 tags for episode %s: %s", instance.episode_number, note)
