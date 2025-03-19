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
    pip install --no-warn-script-location -r requirements.txt && \
    pip install --no-warn-script-location gunicorn psycopg2 mutagen

# Create necessary directories with correct permissions BEFORE copying code
RUN mkdir -p /code/static /code/media /code/logs && \
    chown -R wagtail:wagtail /code

# Copy the project code
COPY . /code/
RUN chown -R wagtail:wagtail /code

# Fix permissions for specific directories that need write access
RUN mkdir -p /code/static/fonts && \
    mkdir -p /code/static/css && \
    mkdir -p /code/static/js && \
    mkdir -p /code/static/admin && \
    mkdir -p /code/static/wagtailadmin && \
    chmod -R 777 /code/static && \
    chmod -R 777 /code/media && \
    chmod -R 777 /code/logs

# Copy entrypoint script
COPY docker-entrypoint.sh /code/
RUN chmod +x /code/docker-entrypoint.sh && \
    chown wagtail:wagtail /code/docker-entrypoint.sh

# Switch to non-root user
USER wagtail

ENTRYPOINT ["/code/docker-entrypoint.sh"]