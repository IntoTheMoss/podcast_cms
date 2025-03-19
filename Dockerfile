FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Create a non-root user
RUN groupadd -r wagtail && useradd -r -g wagtail wagtail

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn psycopg2 mutagen

# Copy the project code
COPY . /code/

# Create necessary directories
RUN mkdir -p /code/static /code/media /code/logs && \
    chown -R wagtail:wagtail /code

# Copy entrypoint script
COPY docker-entrypoint.sh /code/
RUN chmod +x /code/docker-entrypoint.sh

# Switch to non-root user
USER wagtail

ENTRYPOINT ["/code/docker-entrypoint.sh"]