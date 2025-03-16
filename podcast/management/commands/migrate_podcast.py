import os
import os.path
import xml.etree.ElementTree as ET
import requests
import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from podcast.models import PodcastIndexPage, PodcastEpisodePage
from PIL import Image as PILImage
from io import BytesIO
from wagtail.images.models import Image
from wagtail.images import get_image_model
from wagtail.models import Page


class Command(BaseCommand):
    help = "Migrate existing podcast episodes from feed.xml to Wagtail CMS"
    MEDIA_ROOT = settings.MEDIA_ROOT

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, help="Limit the number of episodes to migrate"
        )
        parser.add_argument(
            "--offset", type=int, default=0, help="Skip the first N episodes"
        )
        parser.add_argument(
            "--reverse", action="store_true", help="Process oldest episodes first"
        )

    def handle(self, *args, **options):
        # Find the PodcastIndexPage or create if it doesn't exist
        podcast_index = PodcastIndexPage.objects.live().first()

        if not podcast_index:
            self.stdout.write(
                self.style.WARNING("No PodcastIndexPage found. Creating one...")
            )

            # Find the home page to add the podcast index under
            home_page = Page.objects.filter(slug="home").first()

            if not home_page:
                self.stdout.write(
                    self.style.ERROR(
                        "No home page found. Cannot create PodcastIndexPage."
                    )
                )
                return

            # Create a new podcast index
            podcast_index = PodcastIndexPage(
                title="Podcast",
                slug="podcast",
                intro="A sunken raft of weeds woven into a verdant morass of sound, song and story.",
            )

            # Add to the home page
            home_page.add_child(instance=podcast_index)

            # Publish the page
            revision = podcast_index.save_revision()
            revision.publish()

            self.stdout.write(self.style.SUCCESS("Created new PodcastIndexPage"))

        podcast_index = PodcastIndexPage.objects.live().first()
        if not podcast_index:
            self.stdout.write(
                self.style.ERROR(
                    "Failed to create or retrieve PodcastIndexPage. Aborting."
                )
            )
            return

        # Fetch the XML feed from the URL
        feed_url = "https://intothemoss.com/feed.xml"
        self.stdout.write(f"Fetching feed from {feed_url}")

        try:
            response = requests.get(feed_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            feed_content = response.content
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching feed: {e}"))
            return

        # Parse the XML feed from the content
        try:
            root = ET.fromstring(feed_content)
        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f"Error parsing XML feed: {e}"))
            return

        namespace = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

        # Get options
        limit = options.get("limit")
        offset = options.get("offset", 0)
        reverse = options.get("reverse", False)

        # Process items
        items = root.findall(".//channel/item")
        total_available = len(items)

        # Reverse if needed (to process oldest first)
        if reverse:
            items = list(reversed(items))

        # Apply offset and limit
        working_items = items[offset:]
        if limit:
            working_items = working_items[:limit]

        total_processing = len(working_items)

        self.stdout.write(
            f"Found {total_available} episodes, processing {total_processing} (offset: {offset}, limit: {limit or 'none'})"
        )

        for i, item in enumerate(working_items):
            # Extract information from XML
            title = item.find("title").text
            description = item.find("description").text
            enclosure = item.find("enclosure")
            audio_url = enclosure.get("url")
            audio_filename = os.path.basename(audio_url)
            guid = item.find("guid").text
            pub_date_str = item.find("pubDate").text

            # Get unique episode number from audio filename (e.g., 196.mp3 -> 196)
            try:
                episode_number = int(audio_filename.split(".")[0])
            except (ValueError, IndexError):
                self.stdout.write(
                    self.style.WARNING(
                        f"Couldn't extract episode number from filename: {audio_filename}"
                    )
                )
                episode_number = total_available - i if not reverse else i + 1

            # Parse season-specific episode number (episode within season)
            season_episode_elem = item.find(".//itunes:episode", namespace)
            season_episode_number = (
                int(season_episode_elem.text)
                if season_episode_elem is not None and season_episode_elem.text
                else None
            )

            # Parse season number
            season_number = item.find(".//itunes:season", namespace)
            season_number = (
                int(season_number.text)
                if season_number is not None and season_number.text
                else 1
            )

            # If no season episode number was found, set a default
            if season_episode_number is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"No season episode number found for episode {episode_number}. Using default."
                    )
                )
                season_episode_number = 1

            # Parse duration
            duration_elem = item.find(".//itunes:duration", namespace)
            if duration_elem is not None and duration_elem.text:
                duration_str = duration_elem.text
                try:
                    if "." in duration_str:
                        minutes, seconds = duration_str.split(".")
                        duration_in_seconds = int(float(minutes)) * 60 + int(
                            float(seconds)
                        )
                    else:
                        duration_in_seconds = int(float(duration_str))
                except ValueError:
                    duration_in_seconds = 840  # Default 14 minutes
            else:
                duration_in_seconds = 840  # Default if no duration found

            # Generate a slug for the page
            slug = f"episode-{episode_number:03d}"

            # Check if episode already exists
            if PodcastEpisodePage.objects.filter(guid=guid).exists():
                self.stdout.write(
                    f"Episode {episode_number} ('{title}') already exists. Skipping."
                )
                continue

            # Parse publication date
            try:
                # Attempt to parse date in format: 'Thu, 15 Feb 2024 18:30:00 +0000'
                pub_date = datetime.datetime.strptime(
                    pub_date_str, "%a, %d %b %Y %H:%M:%S %z"
                )
            except ValueError:
                try:
                    # Alternative format sometimes used
                    pub_date = datetime.datetime.strptime(
                        pub_date_str, "%a, %d %b %Y %H:%M:%S"
                    ).replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    self.stdout.write(
                        f"Could not parse date '{pub_date_str}'. Using current date."
                    )
                    pub_date = datetime.datetime.now(datetime.timezone.utc)

            # Check for local audio file first
            audio_content = None
            local_audio_path = os.path.join(self.MEDIA_ROOT, "episodes", audio_filename)
            self.stdout.write(f"Checking for local audio file: {local_audio_path}")
            if os.path.exists(local_audio_path):
                self.stdout.write(
                    f"Using local audio file for episode {episode_number}: {local_audio_path}"
                )
                with open(local_audio_path, "rb") as f:
                    audio_content = f.read()
            else:
                # Fall back to downloading if local file not found
                self.stdout.write(
                    f"Downloading audio for episode {episode_number}: {audio_url}"
                )
                try:
                    audio_response = requests.get(audio_url, stream=True)
                    audio_response.raise_for_status()
                    audio_content = audio_response.content
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error downloading audio: {e}"))
                    continue

            # Get image URL
            image_elem = item.find(".//itunes:image", namespace)
            cover_image = None

            if image_elem is not None:
                image_url = image_elem.get("href")
                image_filename = os.path.basename(image_url)
                image_title = f"Episode {episode_number} Cover"

                # Check for local image file first
                local_image_path = os.path.join(
                    self.MEDIA_ROOT, "original_images", image_filename
                )
                self.stdout.write(f"Checking for local image file: {local_image_path}")

                if os.path.exists(local_image_path):
                    self.stdout.write(
                        f"Using local image file for episode {episode_number}: {local_image_path}"
                    )
                    # Create image with local file
                    image_title = f"Episode {episode_number} Cover"
                    try:
                        # Use Wagtail's built-in method to create the image
                        ImageModel = get_image_model()
                        with open(local_image_path, "rb") as f:
                            cover_image = ImageModel.objects.create(
                                title=image_title, file=File(f, name=image_filename)
                            )
                        self.stdout.write(
                            f"Created image from local file: {cover_image.id}, dimensions: {cover_image.width}x{cover_image.height}"
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error creating image from local file: {e}"
                            )
                        )
                else:
                    # Download image if local file not found
                    self.stdout.write(f"Downloading cover image: {image_url}")
                    try:
                        image_response = requests.get(image_url)
                        image_response.raise_for_status()
                        image_content = image_response.content

                        # Save to temporary file
                        with NamedTemporaryFile(
                            delete=False, suffix=".jpg"
                        ) as temp_file:
                            temp_file.write(image_content)
                            temp_file_path = temp_file.name

                        try:
                            # Use Wagtail's built-in method to create the image
                            ImageModel = get_image_model()
                            with open(temp_file_path, "rb") as f:
                                cover_image = ImageModel.objects.create(
                                    title=image_title, file=File(f, name=image_filename)
                                )
                            self.stdout.write(
                                f"Created image from download: {cover_image.id}, dimensions: {cover_image.width}x{cover_image.height}"
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"Error creating image: {e}")
                            )
                        finally:
                            # Clean up the temporary file
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error downloading image: {e}")
                        )

            # Prepare audio file
            if audio_content:
                # Create a temporary file to hold the audio content
                audio_temp = NamedTemporaryFile(delete=False, suffix=".mp3")
                audio_temp.write(audio_content)
                audio_temp.close()

                try:
                    # Create the episode with all required fields
                    episode = PodcastEpisodePage(
                        title=title,
                        slug=slug,
                        episode_number=episode_number,
                        season_number=season_number,
                        season_episode_number=season_episode_number,  # Added field
                        publication_date=pub_date,
                        description=description,
                        transcript="",  # Empty transcript
                        cover_image=cover_image,
                        duration_in_seconds=duration_in_seconds,
                        explicit_content=False,
                        guid=guid,
                    )

                    # Assign the audio file before adding as child
                    with open(audio_temp.name, "rb") as f:
                        # Create a Django File object
                        django_file = File(f, name=audio_filename)
                        episode.audio_file = django_file

                        # Now add the child (which will save the model)
                        page = podcast_index.add_child(instance=episode)

                    # Make sure it's published
                    revision = page.save_revision()
                    revision.publish()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Migrated episode {episode_number} (S{season_number}E{season_episode_number}): {title}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating episode: {e}"))
                finally:
                    # Clean up the temporary file
                    if os.path.exists(audio_temp.name):
                        os.unlink(audio_temp.name)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"No audio content found for episode {episode_number}. Skipping."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Migration complete!"))
