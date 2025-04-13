import datetime
from django.core.management.base import BaseCommand
from podcast.models import PodcastEpisodePage


class Command(BaseCommand):
    help = "Fix publication dates to match the dates in the guid field"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all podcast episodes
        episodes = PodcastEpisodePage.objects.all()
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for episode in episodes:
            # Skip episodes without a guid or with incorrect guid format
            if not episode.guid or not episode.guid.startswith('itm'):
                self.stdout.write(
                    self.style.WARNING(f"Skipping episode {episode.id} ({episode.title}): Invalid or missing guid '{episode.guid}'")
                )
                skipped_count += 1
                continue
            
            try:
                # Extract date from guid (format: "itm20250214")
                date_str = episode.guid[3:]  # Remove "itm" prefix
                
                # Parse the date string - expected format is YYYYMMDD
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                # Create datetime with 17:30 UTC time
                new_date = datetime.datetime(year, month, day, 17, 30, 0, 
                                            tzinfo=datetime.timezone.utc)
                
                # Display the change
                current_date = episode.publication_date
                self.stdout.write(f"Episode {episode.episode_number} ({episode.title}):")
                self.stdout.write(f"  GUID: {episode.guid}")
                self.stdout.write(f"  Current date: {current_date}")
                self.stdout.write(f"  New date: {new_date}")
                
                # Check if update is needed - compare dates only, not time
                if current_date and current_date.date() == new_date.date():
                    self.stdout.write(self.style.SUCCESS("  No change needed, date portion already matches"))
                    skipped_count += 1
                    continue
                
                # Update the publication date if not in dry-run mode
                if not dry_run:
                    episode.publication_date = new_date
                    episode.save(update_fields=['publication_date'])
                    self.stdout.write(self.style.SUCCESS("  Updated successfully"))
                else:
                    self.stdout.write(self.style.WARNING("  Would update (dry run)"))
                
                updated_count += 1
                
            except (ValueError, IndexError) as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing episode {episode.id} ({episode.title}): {e}")
                )
                error_count += 1
        
        # Print summary
        self.stdout.write("\nSummary:")
        if dry_run:
            self.stdout.write(f"Would update {updated_count} episodes")
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} episodes"))
        self.stdout.write(f"Skipped {skipped_count} episodes")
        self.stdout.write(f"Errors encountered: {error_count}")
