# Into the Moss Podcast CMS

A Django/Wagtail-based content management system for the "Into the Moss" podcast - a 14-minute drift through original music, soundscapes and liminal yarns, broadcast on London's Resonance 104.4 FM.

## Features

- **Episode Management**: Create and manage podcast episodes with metadata, audio files, and transcripts
- **RSS Feed Generation**: Automatic iTunes-compatible podcast feed with proper metadata
- **Audio Validation**: Ensures only MP3 files can be uploaded for episodes
- **Season Organization**: Support for both sequential and season-specific episode numbering
- **Media Management**: Local development storage with DigitalOcean Spaces integration for production
- **Automatic Duration Detection**: Uses mutagen to extract audio duration from MP3 files
- **Wagtail CMS**: Full-featured content management with user-friendly admin interface

## Requirements

- Python 3.9+
- Django 5.1+
- Wagtail 6.4+
- Virtual environment (recommended)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd podcast_cms
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
```

For production, add DigitalOcean Spaces configuration:

```env
SPACES_KEY=your-spaces-key
SPACES_SECRET=your-spaces-secret
SPACES_BUCKET=your-bucket-name
SPACES_REGION=fra1
```

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000/admin` to access the Wagtail admin interface.

## Usage

### Creating Episodes

1. Log into the Wagtail admin
2. Navigate to the Podcast Index page
3. Add new episode pages with:
   - Episode number and season information
   - MP3 audio file (validated automatically)
   - Cover image (1400x1400px recommended)
   - Description and transcript
   - Publication date

### RSS Feed

The podcast RSS feed is automatically generated and includes:
- iTunes-compatible metadata
- Episode enclosures with proper MIME types
- Category information for podcast directories
- Owner and contact information

### Management Commands

```bash
# Migrate episodes from existing XML feed
python manage.py migrate_podcast [--limit N] [--offset N]

# Fix episode slugs to use zero-padded format
python manage.py fix_episode_slugs

# Fix publication dates for episodes
python manage.py fix_publication_dates
```

## Deployment

### Production Setup

1. Set environment variables for production
2. Configure database (PostgreSQL recommended)
3. Set up DigitalOcean Spaces for media storage
4. Run deployment script:

```bash
./deploy.sh
```

The deployment script handles:
- Git pull
- Dependency installation
- Database migrations
- Static file collection
- Server restart (Gunicorn + Nginx)

## Project Structure

```
podcast_cms/
├── intothemoss_cms/          # Django project configuration
│   ├── settings.py           # Environment-based configuration
│   └── templates/            # Base templates
├── podcast/                  # Main podcast app
│   ├── models.py            # Episode and index page models
│   ├── views.py             # RSS feed generation
│   └── management/commands/ # Custom management commands
├── home/                    # Basic site structure
│   └── models.py           # Home, About, Contact pages
├── search/                  # Wagtail search functionality
├── media/                   # Local media storage (dev)
└── requirements.txt         # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is part of the "Into the Moss" podcast production.