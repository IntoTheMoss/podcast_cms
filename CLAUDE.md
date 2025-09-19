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

### Environment Configuration

Key environment variables:
- `DEBUG` - Enable/disable debug mode
- `DATABASE_URL` - Database connection string
- `DJANGO_SECRET_KEY` - Django secret key
- `SPACES_KEY`, `SPACES_SECRET`, `SPACES_BUCKET` - DigitalOcean Spaces configuration
- `WAGTAILADMIN_BASE_URL` - Base URL for Wagtail admin

### Dependencies

The project uses modern Django/Wagtail versions with key dependencies:
- Django 5.1.7 with Wagtail 6.4.1
- mutagen for audio metadata extraction
- Pillow for image processing
- psycopg2-binary for PostgreSQL support
- django-environ for environment management