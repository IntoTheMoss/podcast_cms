# Scheduled Publishing Setup

This project now supports scheduled publishing of podcast episodes using Wagtail's built-in functionality.

## How It Works

When you set a `publication_date` for a podcast episode:
- The episode's `go_live_at` field is automatically set to match
- The episode page will remain unpublished (in draft or scheduled state) until the scheduled time
- At the scheduled time, Wagtail will automatically publish the page
- Once published, the episode appears on your site and in the RSS feed

## Server Setup (Cron Job)

To enable automatic publishing, you need to run Wagtail's `publish_scheduled_pages` management command regularly on your server.

### 1. Set up a cron job

SSH into your server and edit your crontab:

```bash
crontab -e
```

Add this line to run the command every 10 minutes:

```cron
*/10 * * * * cd /path/to/your/podcast_cms && /path/to/your/venv/bin/python manage.py publish_scheduled_pages >> /var/log/wagtail_scheduled.log 2>&1
```

**Important**: Replace the paths:
- `/path/to/your/podcast_cms` - Your project directory
- `/path/to/your/venv/bin/python` - Your virtual environment's Python binary

Example for a typical setup:
```cron
*/10 * * * * cd /home/youruser/podcast_cms && /home/youruser/podcast_cms/venv/bin/python manage.py publish_scheduled_pages >> /var/log/wagtail_scheduled.log 2>&1
```

### 2. Alternative: Run every minute for more precise scheduling

If you want episodes to publish within 1 minute of their scheduled time:

```cron
* * * * * cd /path/to/your/podcast_cms && /path/to/your/venv/bin/python manage.py publish_scheduled_pages >> /var/log/wagtail_scheduled.log 2>&1
```

### 3. Verify the cron job is working

Check the log file to ensure it's running:

```bash
tail -f /var/log/wagtail_scheduled.log
```

## Using Scheduled Publishing

### In the Wagtail Admin:

1. Create or edit a podcast episode page
2. Set the **Publication Date** field to your desired publish time
3. Click the **Publish** button dropdown (▼) and select **"Schedule publishing"**
4. Verify the scheduled time matches your publication date
5. Click **"Schedule publishing"** to confirm

The page will now be in "Scheduled" status and will automatically go live at the specified time.

### Important Notes:

- Episodes in "Draft" status will NOT be automatically published, even with a publication date set
- You must explicitly schedule them using the "Schedule publishing" option
- The RSS feed and website will automatically show the episode once it goes live
- You can edit scheduled pages at any time before they go live
- To cancel scheduling, use "Publish" > "Cancel scheduled publish"

## Testing Scheduled Publishing

To test that everything works:

1. Create a test episode with a publication date 2-3 minutes in the future
2. Schedule it for publishing
3. Wait for the scheduled time
4. Check your website and RSS feed to confirm the episode appeared

## Troubleshooting

**Episode isn't publishing automatically:**
- Check the cron job is running: `tail -f /var/log/wagtail_scheduled.log`
- Verify the page status is "Scheduled" (not "Draft")
- Ensure the `go_live_at` date has passed
- Try running manually: `python manage.py publish_scheduled_pages`

**Multiple episodes publishing at once:**
- This is normal if the cron job wasn't running
- All overdue scheduled pages will publish when the command next runs
