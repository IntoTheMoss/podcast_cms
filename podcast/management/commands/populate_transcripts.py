import os
from django.core.management.base import BaseCommand
from django.conf import settings
from podcast.models import PodcastEpisodePage


class Command(BaseCommand):
    help = "Populate episode transcripts and descriptions from text files in the texts/ folder"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force overwrite existing transcripts and descriptions",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--episode",
            type=int,
            help="Process only a specific episode number",
        )

    def handle(self, *args, **options):
        force = options.get("force", False)
        dry_run = options.get("dry_run", False)
        specific_episode = options.get("episode", None)
        
        # Path to texts folder
        texts_dir = os.path.join(settings.BASE_DIR, "texts")
        
        if not os.path.exists(texts_dir):
            self.stdout.write(
                self.style.ERROR(f"Texts directory not found: {texts_dir}")
            )
            return

        # Get all episodes or specific episode
        if specific_episode:
            episodes = PodcastEpisodePage.objects.filter(episode_number=specific_episode)
        else:
            episodes = PodcastEpisodePage.objects.all()

        if not episodes.exists():
            if specific_episode:
                self.stdout.write(
                    self.style.ERROR(f"No episode found with number: {specific_episode}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("No episodes found in the database")
                )
            return

        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f"Processing {episodes.count()} episodes...")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        for episode in episodes:
            # Generate expected filename with zero-padding
            filename = f"{episode.episode_number:03d}.txt"
            file_path = os.path.join(texts_dir, filename)
            
            # Check if text file exists
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f"Text file not found for Episode {episode.episode_number}: {filename}")
                )
                skipped_count += 1
                continue

            try:
                # Read the text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Skip empty files
                if not content:
                    self.stdout.write(
                        self.style.WARNING(f"Empty text file for Episode {episode.episode_number}: {filename}")
                    )
                    skipped_count += 1
                    continue

                # Check if we should update transcript
                should_update_transcript = force or not episode.transcript or episode.transcript.strip() == ""
                
                # Check if we should update description
                should_update_description = force or not episode.description or episode.description.strip() == ""

                if not should_update_transcript and not should_update_description:
                    self.stdout.write(
                        f"Episode {episode.episode_number}: Both transcript and description already exist (use --force to overwrite)"
                    )
                    skipped_count += 1
                    continue

                # Extract description (first paragraph/section) and full transcript
                description_text = self.extract_description(content)
                transcript_text = content

                updates_made = []

                if should_update_transcript:
                    if not dry_run:
                        episode.transcript = transcript_text
                    updates_made.append("transcript")

                if should_update_description:
                    if not dry_run:
                        episode.description = description_text
                    updates_made.append("description")

                # Save the episode if not dry run
                if not dry_run and updates_made:
                    episode.save(update_fields=["transcript", "description"])

                if updates_made:
                    updates_text = " and ".join(updates_made)
                    action = "Would update" if dry_run else "Updated"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Episode {episode.episode_number}: {action} {updates_text} from {filename}"
                        )
                    )
                    updated_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing Episode {episode.episode_number}: {str(e)}"
                    )
                )
                error_count += 1

        # Summary
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN COMPLETE"))
            self.stdout.write(f"Would update: {updated_count} episodes")
        else:
            self.stdout.write(self.style.SUCCESS(f"OPERATION COMPLETE"))
            self.stdout.write(f"Updated: {updated_count} episodes")
        
        self.stdout.write(f"Skipped: {skipped_count} episodes")
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count} episodes"))

    def extract_description(self, content):
        """
        Extract a suitable description from the full content.
        Takes the first paragraph or first 200 characters, whichever is shorter.
        """
        # Split into paragraphs and take the first non-empty one
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # Fallback to first 200 characters
            return content[:200] + "..." if len(content) > 200 else content
        
        first_paragraph = paragraphs[0]
        
        # If the first paragraph is very long, truncate it
        if len(first_paragraph) > 300:
            # Find a good place to cut (at sentence end)
            sentences = first_paragraph.split('. ')
            description = sentences[0]
            
            # Add more sentences if the description is too short
            for i, sentence in enumerate(sentences[1:], 1):
                potential_desc = '. '.join(sentences[:i+1]) + '.'
                if len(potential_desc) > 250:
                    break
                description = potential_desc
            
            # Ensure it ends properly
            if not description.endswith('.'):
                description += "..."
        else:
            description = first_paragraph
        
        return description