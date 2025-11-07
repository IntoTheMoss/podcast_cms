from wagtail.admin.forms import WagtailAdminPageForm


class PodcastEpisodePageForm(WagtailAdminPageForm):
    """Custom form for PodcastEpisodePage that adds dynamic placeholders."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only add placeholders for new instances (not editing)
        if not self.instance.pk:
            suggested = self.instance.get_suggested_values()

            # Add placeholders to episode information fields (not publication_date to avoid interfering with date picker)
            if "episode_number" in self.fields:
                self.fields["episode_number"].widget.attrs["placeholder"] = str(
                    suggested["episode_number"]
                )

            if "season_number" in self.fields:
                self.fields["season_number"].widget.attrs["placeholder"] = str(
                    suggested["season_number"]
                )

            if "season_episode_number" in self.fields:
                self.fields["season_episode_number"].widget.attrs["placeholder"] = str(
                    suggested["season_episode_number"]
                )

            # Add dynamic help text for publication date
            if "publication_date" in self.fields:
                self.fields["publication_date"].help_text = (
                    f"When the episode was or should be published (suggested: {suggested['publication_date']})"
                )

            if "cover_image" in self.fields:
                self.fields["cover_image"].help_text = (
                    f"Episode cover image (1400x1400px please). Name it: {suggested['episode_number']}.jpg"
                )

            if "audio_file" in self.fields:
                self.fields["audio_file"].help_text = (
                    f"MP3 audio file (under 40MB). Name it: {suggested['episode_number']}.mp3"
                )
