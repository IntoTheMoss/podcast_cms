from django.db import models
from django.core.validators import MinValueValidator
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from modelcluster.fields import ParentalKey
from django.utils.functional import cached_property


class PodcastIndexPage(Page):
    """Landing page for the podcast."""
    intro = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        # Add all published episodes, ordered by episode number
        context['episodes'] = PodcastEpisodePage.objects.live().order_by('-episode_number')
        return context
    
    # Allow only podcast episode pages as children
    subpage_types = ['podcast.PodcastEpisodePage']


class PodcastEpisodePage(Page):
    """Individual podcast episode page."""
    episode_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Episode number (must be unique)"
    )
    season_number = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1)],
        help_text="Season number"
    )
    publication_date = models.DateTimeField(
        help_text="When the episode was or should be published"
    )
    description = RichTextField(
        help_text="Brief description of the episode (appears in RSS feed)"
    )
    transcript = RichTextField(
        blank=True,
        help_text="Full transcript of the episode"
    )
    cover_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, 
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Episode cover image (1400x1400px recommended)"
    )
    audio_file = models.FileField(
        upload_to='episodes/',
        help_text="MP3 audio file"
    )
    duration_in_seconds = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Duration in seconds (will be calculated automatically if blank)"
    )
    explicit_content = models.BooleanField(
        default=False,
        help_text="Mark if episode contains explicit content"
    )
    
    # Fields used for RSS feed generation
    guid = models.CharField(
        max_length=64, 
        blank=True,
        help_text="Unique identifier (will be generated automatically if blank)"
    )
    
    # Search settings
    search_fields = Page.search_fields + [
        index.SearchField('title'),
        index.SearchField('description'),
        index.SearchField('transcript'),
        index.FilterField('episode_number'),
        index.FilterField('season_number'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('episode_number'),
            FieldPanel('season_number'),
            FieldPanel('publication_date'),
        ], heading="Episode Information"),
        FieldPanel('description'),
        FieldPanel('transcript'),
        FieldPanel('cover_image'),
        FieldPanel('audio_file'),
        FieldPanel('explicit_content'),
    ]
    
    # Parent page / subpage type rules
    parent_page_types = ['podcast.PodcastIndexPage']
    subpage_types = []
    
    @cached_property
    def audio_url(self):
        """Return the full URL to the audio file."""
        from django.conf import settings
        return f"{settings.MEDIA_URL}{self.audio_file}"
    
    def save(self, *args, **kwargs):
        # Generate GUID if not provided (you might want to adapt this)
        if not self.guid:
            from datetime import datetime
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
    page = ParentalKey('podcast.PodcastIndexPage', related_name='platform_links')
    title = models.CharField(max_length=255)
    url = models.URLField()
    
    panels = [
        FieldPanel('title'),
        FieldPanel('url'),
    ]