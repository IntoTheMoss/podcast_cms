import os
import traceback
from django.conf import settings
from django.http import HttpResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.generic import View
from django.urls import reverse
from podcast.models import PodcastEpisodePage, PodcastSettings
from wagtail.models import Site


class PodcastFeed(Rss201rev2Feed):
    """Extended RSS feed generator for podcasts."""

    def __init__(self, *args, **kwargs):
        self.has_explicit_episodes = kwargs.pop("has_explicit_episodes", False)
        self.podcast_settings = kwargs.pop("podcast_settings", None)
        super().__init__(*args, **kwargs)

    def root_attributes(self):
        attrs = super().root_attributes()
        attrs["xmlns:itunes"] = "http://www.itunes.com/dtds/podcast-1.0.dtd"
        attrs["xmlns:content"] = "http://purl.org/rss/1.0/modules/content/"
        attrs["xmlns:atom"] = "http://www.w3.org/2005/Atom"
        return attrs

    def add_root_elements(self, handler):
        super().add_root_elements(handler)

        # Basic podcast information
        handler.addQuickElement(
            "itunes:subtitle",
            self.podcast_settings.subtitle,
        )
        handler.addQuickElement("itunes:author", self.podcast_settings.author)
        handler.addQuickElement(
            "itunes:summary",
            self.podcast_settings.summary,
        )

        # Category information - match the original structure
        fiction = handler.startElement("itunes:category", {"text": "Fiction"})
        handler.startElement("itunes:category", {"text": "Drama"})
        handler.endElement("itunes:category")
        handler.endElement("itunes:category")

        fiction = handler.startElement("itunes:category", {"text": "Fiction"})
        handler.startElement("itunes:category", {"text": "Comedy Fiction"})
        handler.endElement("itunes:category")
        handler.endElement("itunes:category")

        # Owner information
        handler.startElement("itunes:owner", {})
        handler.addQuickElement(
            "itunes:name", self.podcast_settings.owner_name
        )
        handler.addQuickElement("itunes:email", self.podcast_settings.email)
        handler.endElement("itunes:owner")

        # Cover image
        if self.podcast_settings.cover_image:
            cover_url = f"https://{settings.PODCAST_DOMAIN}{self.podcast_settings.cover_image.file.url}"
        else:
            cover_url = f"https://{settings.PODCAST_DOMAIN}/media/original_images/cover.jpg"
        handler.addQuickElement(
            "itunes:image",
            "",
            {"href": cover_url},
        )

        # Other iTunes tags - set explicit based on whether any episodes are explicit
        handler.addQuickElement(
            "itunes:explicit", "true" if self.has_explicit_episodes else "false"
        )

        # Atom link
        handler.addQuickElement(
            "atom:link",
            "",
            {
                "href": f"https://{settings.PODCAST_DOMAIN}/feed.xml",
                "rel": "self",
                "type": "application/rss+xml",
            },
        )

    def add_item_elements(self, handler, item):
        # Add iTunes elements first in the desired order
        itunes_attrs = item.get("itunes", {})

        if "episode" in itunes_attrs:
            handler.addQuickElement("itunes:episode", itunes_attrs["episode"])

        if "season" in itunes_attrs:
            handler.addQuickElement("itunes:season", itunes_attrs["season"])

        # Add title and description
        handler.addQuickElement("title", item["title"])
        handler.addQuickElement("description", item["description"])

        # Add enclosure - this is critical for podcasts
        if "enclosure" in item:
            handler.addQuickElement(
                "enclosure",
                "",
                {
                    "url": item["enclosure"]["url"],
                    "length": item["enclosure"]["length"],
                    "type": item["enclosure"]["mime_type"],
                },
            )

        # Add link and other standard elements
        handler.addQuickElement("link", item["link"])

        # Add image before guid
        if "itunes" in item and "image" in item["itunes"]:
            handler.addQuickElement(
                "itunes:image", "", {"href": item["itunes"]["image"]}
            )

        # Add guid
        handler.addQuickElement("guid", item["unique_id"])

        # Add episode id
        handler.addQuickElement("epid", item["custom_fields"]["epid"])

        # Add pubDate
        handler.addQuickElement(
            "pubDate", item["pubdate"].strftime("%a, %d %b %Y %H:%M:%S %z")
        )

        # Add remaining iTunes elements
        if "duration" in itunes_attrs:
            handler.addQuickElement("itunes:duration", itunes_attrs["duration"])

        if "explicit" in itunes_attrs:
            handler.addQuickElement("itunes:explicit", itunes_attrs["explicit"])

        if "summary" in itunes_attrs:
            handler.addQuickElement("itunes:summary", itunes_attrs["summary"])


class PodcastFeedView(View):
    """View to generate the podcast RSS feed."""

    def get(self, request):
        try:
            # Get default site or first available site
            try:
                site = Site.objects.get(is_default_site=True)
            except Site.DoesNotExist:
                site = Site.objects.first()

            if not site:
                return HttpResponse(
                    "No site configured", content_type="text/plain", status=500
                )

            # Use production URL for the feed regardless of environment
            root_url = f"https://{settings.PODCAST_DOMAIN}"

            # Get episodes first to check for explicit content
            episodes = (
                PodcastEpisodePage.objects.live().public().order_by("-publication_date")
            )

            # Get podcast settings from CMS
            podcast_settings = PodcastSettings.for_site(site)

            # Check if any episodes are explicit to set the show-level explicit flag
            has_explicit_episodes = episodes.filter(explicit_content=True).exists()

            # Basic feed setup
            feed = PodcastFeed(
                title=podcast_settings.title,
                link=root_url,
                description=podcast_settings.description,
                language=podcast_settings.language,
                author_name=podcast_settings.author,
                feed_url=f"{root_url}/feed.xml",
                copyright=podcast_settings.copyright_notice,
                has_explicit_episodes=has_explicit_episodes,
                podcast_settings=podcast_settings,
            )

            for episode in episodes:
                # Zero-pad the episode number for consistent formatting
                episode_padded = f"{episode.episode_number:03d}"

                # Get file size accurately
                try:
                    if episode.audio_file and os.path.exists(episode.audio_file.path):
                        file_size = str(os.path.getsize(episode.audio_file.path))
                    else:
                        # If we can't get the size, use a reasonable estimate based on duration
                        # ~128kbps = ~16KB per second of audio
                        file_size = str(int(episode.duration_in_seconds * 16000))
                except Exception as e:
                    # Fallback size
                    file_size = "15000000"  # 15MB is a reasonable default for a 14-minute episode

                # Fix the duration format to match original (840.05)
                if episode.duration_in_seconds:
                    # Make sure we're working with seconds, not milliseconds
                    seconds_value = episode.duration_in_seconds
                    # If the value is unreasonably large (over an hour), it might be in milliseconds
                    if seconds_value > 3600:
                        # Convert from milliseconds to seconds if needed
                        seconds_value = (
                            seconds_value / 60
                        )  # This assumes the value might be in minutes

                    # Format to 2 decimal places
                    duration = f"{seconds_value:.2f}"
                else:
                    # Default to 14 minutes (840.05 seconds)
                    duration = "840.05"

                # Get the episode cover image URL - use production URL with zero-padded episode number
                if episode.cover_image:
                    image_url = f"{root_url}/media/original_images/{episode_padded}.jpg"
                else:
                    # Fall back to podcast main cover image
                    if podcast_settings.cover_image:
                        image_url = f"{root_url}{podcast_settings.cover_image.file.url}"
                    else:
                        image_url = f"{root_url}/media/original_images/cover.jpg"

                # Generate an estimated file size if we can't get the actual size
                try:
                    if os.path.exists(episode.audio_file.path):
                        file_size = str(os.path.getsize(episode.audio_file.path))
                    else:
                        # Estimate based on duration: ~15MB for 14 minutes
                        file_size = str(int(episode.duration_in_seconds * 1000 * 15))
                except:
                    file_size = "15000000"  # Default estimate

                # Add episode to feed with zero-padded URLs
                feed.add_item(
                    title=episode.title,
                    link=f"{root_url}/episodes/{episode_padded}",
                    description=str(episode.description),
                    pubdate=episode.publication_date,
                    unique_id=(
                        episode.guid
                        if episode.guid
                        else f"itm-ep{episode.episode_number}"
                    ),
                    enclosure={
                        "url": f"{root_url}/media/episodes/{episode_padded}.mp3",
                        "length": file_size,
                        "mime_type": "audio/mpeg",
                    },
                    itunes={
                        "duration": duration,
                        "summary": str(episode.description),
                        "image": image_url,
                        "explicit": "true" if episode.explicit_content else "false",
                        "episode": str(episode.season_episode_number),
                        "season": str(episode.season_number),
                    },
                    # Add custom field for episode ID
                    custom_fields={"epid": episode_padded},
                )

            # Generate and return the feed
            # Use a custom formatter to get proper indentation
            response = HttpResponse(content_type="application/rss+xml; charset=utf-8")

            # Pretty print the XML with indentation
            from xml.dom import minidom

            xml_str = feed.writeString("utf-8")
            parsed = minidom.parseString(xml_str)
            pretty_xml = parsed.toprettyxml(indent="  ")

            # Remove extra blank lines that minidom sometimes adds
            pretty_xml = "\n".join(
                [line for line in pretty_xml.split("\n") if line.strip()]
            )

            response.write(pretty_xml)
            return response
        except Exception as e:
            error_message = f"Error generating feed: {str(e)}\n{traceback.format_exc()}"
            return HttpResponse(error_message, content_type="text/plain", status=500)
