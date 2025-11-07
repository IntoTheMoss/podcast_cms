from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_admin_menu_item")
def register_podcast_menu_item():
    # Find the podcast index page to get its ID
    from podcast.models import PodcastIndexPage

    podcast_index = PodcastIndexPage.objects.live().first()
    if not podcast_index:
        return None

    return MenuItem(
        "Add Episode",
        reverse(
            "wagtailadmin_pages:add",
            args=["podcast", "podcastepisodepage", podcast_index.id],
        ),
        icon_name="circle-plus",
        order=10,
    )


@hooks.register('before_edit_page')
def add_dynamic_placeholders(request, page):
    """Add dynamic placeholders to episode fields when creating new episodes."""
    # Only apply to PodcastEpisodePage
    from podcast.models import PodcastEpisodePage

    if isinstance(page, PodcastEpisodePage) and not page.pk:
        # Get suggested values
        suggested = page.get_suggested_values()

        # Store in request so we can use it in construct_page_form
        request.suggested_episode_values = suggested


@hooks.register('construct_page_form')
def customize_episode_form(form, request):
    """Customize the page form to add placeholders."""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"construct_page_form called, form fields: {list(form.fields.keys())}")

    # Check if we have suggested values from the before_edit_page hook
    if hasattr(request, 'suggested_episode_values'):
        suggested = request.suggested_episode_values
        logger.info(f"Applying placeholders: {suggested}")

        # Add placeholders to form fields
        if 'episode_number' in form.fields:
            form.fields['episode_number'].widget.attrs['placeholder'] = str(suggested['episode_number'])
            logger.info(f"Set placeholder for episode_number")

        if 'season_number' in form.fields:
            form.fields['season_number'].widget.attrs['placeholder'] = str(suggested['season_number'])

        if 'season_episode_number' in form.fields:
            form.fields['season_episode_number'].widget.attrs['placeholder'] = str(suggested['season_episode_number'])

        if 'publication_date' in form.fields:
            form.fields['publication_date'].widget.attrs['placeholder'] = str(suggested['publication_date'])
    else:
        logger.info("No suggested_episode_values in request")
