"""Re-write ID3 tags on episode audio from the CMS record.

Publishing an episode tags it automatically (see podcast/signals.py). This
command is for the bulk cases: backfilling, or pushing a metadata correction
out to files that are already published.

    python manage.py retag_episodes                 # every live episode
    python manage.py retag_episodes 230 231 232     # specific episodes
    python manage.py retag_episodes --season 17     # a whole season
    python manage.py retag_episodes --since 196     # episode 196 onwards
    python manage.py retag_episodes --dry-run       # report, change nothing
"""

from django.core.management.base import BaseCommand, CommandError

from podcast.id3 import TaggingError, write_tags
from podcast.models import PodcastEpisodePage


class Command(BaseCommand):
    help = "Write ID3 tags into episode MP3s from their CMS metadata."

    def add_arguments(self, parser):
        parser.add_argument(
            "episodes", nargs="*", type=int,
            help="Episode numbers to tag. Omit to tag every live episode.",
        )
        parser.add_argument("--season", type=int, help="Tag one season.")
        parser.add_argument(
            "--since", type=int, help="Tag from this episode number onwards.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="List what would be tagged without writing anything.",
        )

    def handle(self, *args, **options):
        episodes = PodcastEpisodePage.objects.live().order_by("episode_number")

        if options["episodes"]:
            episodes = episodes.filter(episode_number__in=options["episodes"])
        if options["season"] is not None:
            episodes = episodes.filter(season_number=options["season"])
        if options["since"] is not None:
            episodes = episodes.filter(episode_number__gte=options["since"])

        if not episodes.exists():
            raise CommandError("No live episodes matched.")

        dry_run = options["dry_run"]
        tagged, failed = 0, []

        for episode in episodes:
            label = f"ep{episode.episode_number:>3}"
            if dry_run:
                self.stdout.write(
                    f"{label} would tag {episode.title!r} "
                    f"S{episode.season_number}E{episode.season_episode_number}"
                )
                tagged += 1
                continue
            try:
                note = write_tags(episode)
            except TaggingError as exc:
                failed.append((episode.episode_number, str(exc)))
                self.stdout.write(self.style.ERROR(f"{label} FAILED: {exc}"))
            else:
                tagged += 1
                self.stdout.write(f"{label} {note}")

        verb = "would tag" if dry_run else "tagged"
        summary = f"{verb} {tagged} episode(s)"
        if failed:
            self.stdout.write(self.style.ERROR(f"{summary}, {len(failed)} failed"))
            raise CommandError(
                "; ".join(f"ep{n}: {m}" for n, m in failed)
            )
        self.stdout.write(self.style.SUCCESS(summary))
