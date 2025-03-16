import os
from datetime import datetime
from django.http import HttpResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.generic import View
from django.urls import reverse
from podcast.models import PodcastEpisodePage
from wagtail.models import Site


class PodcastFeed(Rss201rev2Feed):
    """Extended RSS feed generator for podcasts."""

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
            "A sunken raft of weeds woven into a verdant morass of sound, song and story",
        )
        handler.addQuickElement("itunes:author", "Into the Moss")
        handler.addQuickElement(
            "itunes:summary",
            "Into the Moss is a 14 minute drift through original music, soundscapes and liminal yarns, broadcast on London's Resonance 104.4 FM",
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
            "itunes:name", "James Baxter, James Ferris, Ben Polhill"
        )
        handler.addQuickElement("itunes:email", "intothemossradio@gmail.com")
        handler.endElement("itunes:owner")

        # Cover image
        handler.addQuickElement(
            "itunes:image",
            "",
            {"href": "https://intothemoss.com/images/intothemoss.jpg"},
        )

        # Other iTunes tags
        handler.addQuickElement("itunes:explicit", "false")

        # Atom link
        handler.addQuickElement(
            "atom:link",
            "",
            {
                "href": "https://intothemoss.com/feed.xml",
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
        # Get the current site
        from wagtail.models import Site

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
        root_url = "https://intothemoss.com"

        # Basic feed setup
        feed = PodcastFeed(
            title="Into the Moss",
            link=root_url,
            description="A sunken raft of weeds woven into a verdant morass of sound, song and story. Broadcast on London's Resonance FM every Thursday, Into the Moss is a 14 minute drift through original music, soundscapes and liminal yarns.",
            language="en-uk",
            author_name="Into the Moss",
            feed_url=f"{root_url}/feed.xml",
            copyright="© Into the Moss 2020-2025",  # Updated year
        )

        # Add episodes to the feed
        episodes = (
            PodcastEpisodePage.objects.live().public().order_by("-publication_date")
        )

        for episode in episodes:
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
                file_size = (
                    "15000000"  # 15MB is a reasonable default for a 14-minute episode
                )

            # Fix the duration format to match original (840.05)
            duration = "840.05"  # Default
            if episode.duration_in_seconds:
                try:
                    duration = f"{episode.duration_in_seconds:.2f}"
                except:
                    pass

            # Get the episode cover image URL - use production URL
            if episode.cover_image:
                image_url = (
                    f"{root_url}/assets/images/jpg/1400/{episode.episode_number}.jpg"
                )
            else:
                image_url = f"{root_url}/images/intothemoss.jpg"

            # Generate an estimated file size if we can't get the actual size
            try:
                if os.path.exists(episode.audio_file.path):
                    file_size = str(os.path.getsize(episode.audio_file.path))
                else:
                    # Estimate based on duration: ~15MB for 14 minutes
                    file_size = str(int(episode.duration_in_seconds * 1000 * 15))
            except:
                file_size = "15000000"  # Default estimate

            # Add episode to feed
            feed.add_item(
                title=episode.title,
                link=f"{root_url}/episodes/{episode.episode_number}",
                description=str(episode.description),
                pubdate=episode.publication_date,
                unique_id=(
                    episode.guid if episode.guid else f"itm-ep{episode.episode_number}"
                ),
                enclosure={
                    "url": f"{root_url}/audio/{episode.episode_number}.mp3",
                    "length": file_size,
                    "mime_type": "audio/mpeg",
                },
                itunes={
                    "duration": duration,
                    "summary": str(episode.description),
                    "image": image_url,
                    "explicit": "false",
                    "episode": (
                        str(episode.season_episode_number)
                        if hasattr(episode, "season_episode_number")
                        and episode.season_episode_number
                        else str(episode.episode_number)
                    ),
                    "season": str(episode.season_number),
                },
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
