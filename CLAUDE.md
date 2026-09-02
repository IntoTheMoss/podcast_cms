# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Development Server
```bash
python manage.py runserver
```

### Database Operations
```bash
# Run database migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### Custom Management Commands
```bash
# Migrate podcast episodes from XML feed to Wagtail CMS
python manage.py migrate_podcast [--limit N] [--offset N]

# Fix episode slugs to use zero-padded format
python manage.py fix_episode_slugs

# Fix publication dates for episodes
python manage.py fix_publication_dates
```

### Deployment
```bash
# Deploy to production (requires server setup)
./deploy.sh
```

## Project Architecture

This is a Django/Wagtail CMS for managing the "Into the Moss" podcast. The project follows a standard Wagtail structure with custom podcast functionality.

### Key Applications

**`podcast_cms/`** - Main Django project configuration
- `settings.py` - Configured for both development (SQLite) and production (PostgreSQL via DATABASE_URL)
- Uses django-environ for environment variable management
- Supports DigitalOcean Spaces for media storage in production

**`podcast/`** - Core podcast management app
- `PodcastIndexPage` - Landing page listing all episodes
- `PodcastEpisodePage` - Individual episode pages with metadata, audio files, and transcripts
- RSS feed generation with iTunes-compatible tags
- Automatic audio duration detection using mutagen
- Episode slugs are automatically formatted as zero-padded numbers (e.g., "001", "002")

**`home/`** - Basic site structure
- `HomePage` - Redirects to podcast index
- `AboutPage` and `ContactPage` - Static content pages
- `PlatformLink` model for external podcast platform links

**`search/`** - Wagtail search functionality

### Media Handling

- Local development: Files stored in `media/` directory
- Production: DigitalOcean Spaces integration with CDN
- Audio files uploaded to `episodes/` subdirectory
- Cover images handled through Wagtail's image system

### RSS Feed

The project generates a custom iTunes-compatible RSS feed at the podcast feed URL. The feed includes:
- Episode metadata (title, description, publication date)
- Audio file enclosures
- iTunes-specific tags for podcast directories
- Episode numbering and season organization

### Episode Management

Episodes have both sequential numbering (`episode_number`) and season-specific numbering (`season_episode_number`). The system automatically:
- Generates slugs from episode numbers
- Creates GUIDs for RSS feed compatibility
- Detects audio duration from MP3 files
- Handles cover image resizing and optimization

#### GUIDs are minted once and must never change

`save()` sets `guid` to `itm<YYYYMMDD>` from `publication_date` **only when
it is blank**. It is never regenerated, so moving an episode's date leaves
the guid behind. That is correct: `guid` is the RSS `unique_id`, and changing
it makes every subscriber's app treat the episode as new — re-downloading it,
often duplicating it in their library.

Episode 200 is the visible case: `guid=itm20250321`, `publication_date=25 Apr
2025`. It was minted for the 21 Mar slot (the next weekly slot after ep199 on
14 Mar), then slipped to 25 Apr and became the season 14 opener instead. The
mismatch is cosmetic and **deliberately left alone**. A guid only has to be
unique and stable, not meaningful. Don't "fix" it.

#### ID3 tags are written from the CMS at publish time

`podcast/id3.py` writes each episode's metadata into its own MP3; the
`page_published` hook in `podcast/signals.py` fires it on every publish, and
`manage.py retag_episodes` handles bulk cases (`--season`, `--since`,
explicit numbers, `--dry-run`). The frame set matches what episodes 1-195
already carried from a pre-Wagtail deployment script.

This exists because Radio Moss reads titles off the files, not the CMS, and
**Icecast keeps displaying whatever title it was last sent** — so an untagged
track showed the *previous* episode's name. Episodes 196-237 shipped untagged
and did this for 18% of the rotation until 2026-09-02.

Two things to preserve: tagging failures are logged and swallowed, never
raised, so a missing file can't block an editorial publish; and re-tagging
runs on *every* publish, which is what pushes a metadata correction out to
files that are already live. Registered in `PodcastConfig.ready()`, so the
app needs a restart (`gunicorn-intothemoss`) for changes to take effect.

Tagging writes in place via `audio_file.path`, so it assumes local disk. If
media ever moves to Spaces it raises a clean `TaggingError` rather than
failing obscurely — see the storage note below.

### Environment Configuration

Key environment variables:
- `DEBUG` - Enable/disable debug mode
- `DATABASE_URL` - Database connection string
- `DJANGO_SECRET_KEY` - Django secret key
- `SPACES_KEY`, `SPACES_SECRET`, `SPACES_BUCKET` - DigitalOcean Spaces configuration
- `WAGTAILADMIN_BASE_URL` - Base URL for Wagtail admin

### Dependencies

The project uses modern Django/Wagtail versions with key dependencies:
- Django 5.2.16 with Wagtail 7.4.2
- mutagen for audio metadata extraction
- Pillow for image processing
- psycopg2-binary for PostgreSQL support
- django-environ for environment management

## Radio Moss

A 24/7 Icecast stream of the shuffled back catalogue, with a player page at
`/radio` (`radio()` in `podcast/views.py`, `radio_page.html`,
`static/js/radio.js`, the `.radio-*` rules in `styles.css`).

The stream is a **separate project** at `/var/www/podcast_radio` (Liquidsoap +
Icecast), not in this repo. Its config lives in `/var/www/podcast_radio/.env`,
read by systemd as an `EnvironmentFile` — setting those variables in a shell
profile does nothing, because the unit does not run a login shell and runs as
`podcast_radio`, not root. Restarting `podcast-radio` drops listeners for
10-20s while Liquidsoap reconnects to Icecast, so batch changes to that file.

### Things that will waste your time

- **Deploying static files.** `STORAGES` uses `ManifestStaticFilesStorage`, so
  production serves hashed filenames. Editing a file under
  `podcast_cms/static/` changes nothing live until `collectstatic` runs. The
  app service is `gunicorn-intothemoss`, not `gunicorn`.
- **`hidden` does nothing on an inline `<svg>`.** The UA stylesheet rule that
  implements it is scoped to the XHTML namespace, so it never matches an SVG
  element. Both icons render. Drive icon visibility from CSS instead — see
  `.radio-button-main.is-playing` and `.radio-button-mute[aria-pressed]`.
- **Icecast already sends `Access-Control-Allow-Origin: *`.** Do not add
  another in the nginx `radio.intothemoss.com` block: two of the header makes
  browsers fail the CORS check outright, which is worse than none.
- **Never let the waveform code touch playback.** `radio.js` once carried a
  heuristic that watched for a flat analyser signal and rebuilt the audio
  element to recover from a tainted graph. It misfired and killed the stream
  about 7s in, and removing the element from the DOM rejected the in-flight
  `play()` promise, so the recovery also painted an error over its own new
  element. Web Audio is now gated on an up-front `fetch` CORS probe and no
  drawing path may pause, reload or replace the element. Keep it that way.
- **A rejected `play()` promise is not necessarily an error.** Pausing or
  reloading an element rejects it with `AbortError`. Check that before
  reporting a failure, and check the attempt has not been superseded.

### Storage note

`settings.py` lines 139-155 configure DigitalOcean Spaces and set the
deprecated `DEFAULT_FILE_STORAGE`, but line 161 sets `STORAGES["default"]` to
`FileSystemStorage` unconditionally. Under Django 5.2 `STORAGES` wins, so the
Spaces branch is dead code. Media is on local disk.

Django never overwrites a colliding upload; `FileSystemStorage` appends a
random suffix (`202_ji3idy2.mp3`). The feed therefore builds enclosure URLs
from `episode.audio_file.url`, never from the episode number, so the feed and
the site always advertise the same file. Do not "tidy" that back into a
number-derived path.

`media/orphaned_episodes/` holds 199 quarantined files that no episode page
references. They are moved, not deleted, pending a decision on episodes 109
and 115, which have files but no pages.

### Not visually verified

The radio page was built and deployed from a server with no browser. Its
markup, assets, endpoints and headers are confirmed; its appearance and
behaviour in a real browser are not. Worth checking with a browser:

1. The waveform's depth and how hard it spikes — `DRIVE` in `radio.js` is the
   dial, tuned by arithmetic rather than by eye.
2. That play/pause and mute/unmute each show exactly one icon.
3. That the stream plays continuously for several minutes without stopping.
4. Whether the analyser is actually feeding the waveform, or it has quietly
   fallen back to the synthetic squiggle — the console says which.
5. Layout at mobile widths, and with `prefers-reduced-motion` set.
