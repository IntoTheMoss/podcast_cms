from django.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey


class HomePage(Page):
    """
    Home page model.
    Since our podcast index will be the main landing page, this is just a redirect to the podcast index.
    """

    # No need to define any fields as the home page will redirect to podcast index

    # Allow creating about, contact, and podcast index pages as children
    subpage_types = ["podcast.PodcastIndexPage", "home.AboutPage", "home.ContactPage"]

    def serve(self, request):
        """Redirect to the podcast index page if it exists."""
        from podcast.models import (
            PodcastIndexPage,
        )  # Import here to avoid circular imports

        # Find the first PodcastIndexPage in the site
        podcast_index = None

        try:
            # First check if there's a direct child that is a PodcastIndexPage
            podcast_index = PodcastIndexPage.objects.child_of(self).live().first()

            # If not found as a direct child, search more broadly
            if not podcast_index:
                podcast_index = PodcastIndexPage.objects.live().first()
        except Exception as e:
            # Fall back to default behavior if any errors occur
            return super().serve(request)

        if podcast_index:
            return podcast_index.serve(request)
        else:
            # Fall back to the default behavior if no podcast index exists yet
            return super().serve(request)


class AboutPage(Page):
    """About page model."""

    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        InlinePanel("platform_links", label="Platform Links"),
    ]

    # Make this a singleton - can only exist once under the home page
    parent_page_types = ["home.HomePage"]
    subpage_types = []


class PlatformLink(Orderable):
    """Links to external platforms where the podcast is available."""

    page = ParentalKey("AboutPage", related_name="platform_links")
    title = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel("title"),
        FieldPanel("url"),
    ]


class ContactPage(Page):
    """Contact page model."""

    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    # Make this a singleton - can only exist once under the home page
    parent_page_types = ["home.HomePage"]
    subpage_types = []
