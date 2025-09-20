from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from modelcluster.fields import ParentalKey
from django.utils.functional import cached_property
import os


def validate_mp3_file(value):
    """Validate that the uploaded file is an MP3."""
    if not value:
        return
    
    # Check file extension
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.mp3':
        raise ValidationError('Only MP3 files are allowed.')
    
    # Check MIME type if available
    if hasattr(value, 'content_type'):
        if value.content_type and not value.content_type.startswith('audio/'):
            raise ValidationError('File must be an audio file.')
    
    # Optional: Check file signature (magic bytes) for MP3
    if hasattr(value, 'read'):
        # Save current position
        current_pos = value.tell() if hasattr(value, 'tell') else 0
        value.seek(0)
        
        # Read first few bytes to check MP3 signature
        header = value.read(3)
        if header and len(header) >= 3:
            # MP3 files typically start with ID3 tag or MP3 frame sync
            if not (header[:3] == b'ID3' or 
                   (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0)):
                # Reset position and raise error
                if hasattr(value, 'seek'):
                    value.seek(current_pos)
                raise ValidationError('File does not appear to be a valid MP3.')
        
        # Reset file position
        if hasattr(value, 'seek'):
            value.seek(current_pos)


class PodcastIndexPage(Page):
    """Landing page for the podcast."""

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        # Add all published episodes, ordered by episode number
        context["episodes"] = PodcastEpisodePage.objects.live().order_by(
            "-episode_number"
        )
        return context

    # Allow only podcast episode pages as children
    subpage_types = ["podcast.PodcastEpisodePage"]


class PodcastEpisodePage(Page):
    # Episode_number is the unique identifier
    episode_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Unique episode number across all seasons",
    )
    # Season-specific episode number
    season_episode_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Episode number within the season",
        null=True,  # Allow null for backward compatibility
        blank=True,
    )
    season_number = models.IntegerField(
        default=1, validators=[MinValueValidator(1)], help_text="Season number"
    )
    publication_date = models.DateTimeField(
        help_text="When the episode was or should be published"
    )
    description = RichTextField(
        help_text="Brief description of the episode (appears in RSS feed)"
    )
    transcript = RichTextField(blank=True, help_text="Full transcript of the episode")
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Episode cover image (1400x1400px recommended)",
    )
    audio_file = models.FileField(
        upload_to="episodes/", 
        help_text="MP3 audio file",
        validators=[validate_mp3_file]
    )
    duration_in_seconds = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Duration in seconds (will be calculated automatically if blank)",
    )
    explicit_content = models.BooleanField(
        default=False, help_text="Mark if episode contains explicit content"
    )

    # Fields used for RSS feed generation
    guid = models.CharField(
        max_length=64,
        blank=True,
        help_text="Unique identifier (will be generated automatically if blank)",
    )

    # Search settings
    search_fields = Page.search_fields + [
        index.SearchField("title"),
        index.SearchField("description"),
        index.SearchField("transcript"),
        index.FilterField("episode_number"),
        index.FilterField("season_number"),
    ]

    # Admin panels
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("episode_number"),
                FieldPanel("season_number"),
                FieldPanel("season_episode_number"),
                FieldPanel("publication_date"),
            ],
            heading="Episode Information",
        ),
        FieldPanel("description"),
        FieldPanel("transcript"),
        FieldPanel("cover_image"),
        FieldPanel("audio_file"),
        FieldPanel("explicit_content"),
    ]

    # Parent page / subpage type rules
    parent_page_types = ["podcast.PodcastIndexPage"]
    subpage_types = []

    @cached_property
    def audio_url(self):
        """Return the full URL to the audio file."""
        from django.conf import settings

        return f"{settings.MEDIA_URL}{self.audio_file}"

    def save(self, *args, **kwargs):
        # Format the slug as episode number with leading zeros as needed
        self.slug = f"{self.episode_number:03d}"

        # Generate GUID if not provided (you might want to adapt this)
        if not self.guid:
            date_str = self.publication_date.strftime("%Y%m%d")
            self.guid = f"itm{date_str}"

        # Set title if not manually set
        if not self.title or self.title == f"Episode {self.episode_number}":
            self.title = f"Episode {self.episode_number}"

        # Try to detect audio duration if not set (requires mutagen)
        if not self.duration_in_seconds and self.audio_file:
            try:
                from mutagen.mp3 import MP3

                audio = MP3(self.audio_file.path)
                self.duration_in_seconds = int(audio.info.length)
            except (ImportError, Exception):
                # Handle case where mutagen is not available or file cannot be read
                pass

        super().save(*args, **kwargs)


# Optional: Add links as a separate model if needed
class PodcastLink(Orderable):
    """External platform links for the podcast (e.g., Spotify, Apple Podcasts)."""

    page = ParentalKey("podcast.PodcastIndexPage", related_name="platform_links")
    title = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel("title"),
        FieldPanel("url"),
    ]


@register_setting
class PodcastSettings(BaseSiteSetting):
    """Site-wide podcast settings that can be managed through the CMS."""

    title = models.CharField(
        max_length=255,
        default="Your Podcast",
        help_text="The name of your podcast"
    )

    subtitle = models.CharField(
        max_length=255,
        default="A sunken raft of weeds woven into a verdant morass of sound, song and story",
        help_text="Short description for podcast directories"
    )

    summary = models.TextField(
        default="Your podcast is a 14 minute drift through original music, soundscapes and liminal yarns",
        help_text="Summary description for iTunes"
    )

    description = models.TextField(
        default="A sunken raft of weeds woven into a verdant morass of sound, song and story. Broadcast on London's Resonance FM every Friday, Your podcast is a 14 minute drift through original music, soundscapes and liminal yarns.",
        help_text="Full description for RSS feed"
    )

    author = models.CharField(
        max_length=255,
        default="Your Name",
        help_text="Author/creator name for the podcast"
    )

    owner_name = models.CharField(
        max_length=255,
        default="Your Name",
        help_text="Owner name for iTunes (can be multiple people)"
    )

    email = models.EmailField(
        default="your@email.com",
        help_text="Contact email for the podcast"
    )

    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Main podcast cover image (1400x1400px recommended)"
    )

    copyright_notice = models.CharField(
        max_length=255,
        default="© Your Podcast 2025",
        help_text="Copyright notice for the podcast"
    )

    language = models.CharField(
        max_length=10,
        default="en-uk",
        help_text="Language code for the podcast (e.g. en-uk, en-us)"
    )

    panels = [
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("subtitle"),
            FieldPanel("author"),
        ], heading="Basic Information"),

        MultiFieldPanel([
            FieldPanel("summary"),
            FieldPanel("description"),
        ], heading="Descriptions"),

        MultiFieldPanel([
            FieldPanel("owner_name"),
            FieldPanel("email"),
            FieldPanel("copyright_notice"),
            FieldPanel("language"),
        ], heading="Contact & Legal"),

        FieldPanel("cover_image"),
    ]

    class Meta:
        verbose_name = "Podcast Settings"
