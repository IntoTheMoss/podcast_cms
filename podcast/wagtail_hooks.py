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
