# podcast/management/commands/fix_episode_slugs.py
from django.core.management.base import BaseCommand
from podcast.models import PodcastEpisodePage


class Command(BaseCommand):
    help = "Fix slugs of podcast episodes to match the episode number format"

    def handle(self, *args, **options):
        episodes = PodcastEpisodePage.objects.all()
        count = 0

        for episode in episodes:
            old_slug = episode.slug
            new_slug = f"{episode.episode_number:03d}"

            if old_slug != new_slug:
                # Update the slug
                episode.slug = new_slug
                episode.save_revision().publish()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated episode {episode.episode_number} slug from '{old_slug}' to '{new_slug}'"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"Updated {count} episode slugs"))
