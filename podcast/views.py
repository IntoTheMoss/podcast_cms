import os
from datetime import datetime
from django.http import HttpResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.generic import View
from django.urls import reverse
from podcast.models import PodcastEpisodePage


class PodcastFeed(Rss201rev2Feed):
    """Extended RSS feed generator for podcasts."""
    
    def root_attributes(self):
        attrs = super().root_attributes()
        attrs['xmlns:itunes'] = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
        attrs['xmlns:content'] = 'http://purl.org/rss/1.0/modules/content/'
        attrs['xmlns:atom'] = 'http://www.w3.org/2005/Atom'
        return attrs
    
    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        
        # Basic podcast information
        handler.addQuickElement('itunes:subtitle', 'A sunken raft of weeds woven into a verdant morass of sound, song and story')
        handler.addQuickElement('itunes:author', 'Into the Moss')
        handler.addQuickElement('itunes:summary', 'Into the Moss is a 14 minute drift through original music, soundscapes and liminal yarns, broadcast on London\'s Resonance 104.4 FM')
        
        # Category information
        handler.startElement('itunes:category', {'text': 'Music'})
        handler.endElement('itunes:category')
        
        # Owner information
        handler.startElement('itunes:owner', {})
        handler.addQuickElement('itunes:name', 'Into the Moss')
        handler.addQuickElement('itunes:email', 'intothemossradio@gmail.com')
        handler.endElement('itunes:owner')
        
        # Cover image
        handler.addQuickElement('itunes:image', '', {'href': 'https://intothemoss.com/static/images/podcast-cover.jpg'})
        
        # Other iTunes tags
        handler.addQuickElement('itunes:explicit', 'false')
        handler.addQuickElement('language', 'en-us')
        
        # Atom link
        handler.addQuickElement('atom:link', '', {
            'href': 'https://intothemoss.com/feed.xml',
            'rel': 'self',
            'type': 'application/rss+xml'
        })
    
    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        
        # Episode-specific iTunes tags
        item_itunes_attrs = item.get('itunes', {})
        
        if 'duration' in item_itunes_attrs:
            handler.addQuickElement('itunes:duration', item_itunes_attrs['duration'])
        
        if 'summary' in item_itunes_attrs:
            handler.addQuickElement('itunes:summary', item_itunes_attrs['summary'])
        
        if 'image' in item_itunes_attrs:
            handler.addQuickElement('itunes:image', '', {'href': item_itunes_attrs['image']})
        
        if 'explicit' in item_itunes_attrs:
            handler.addQuickElement('itunes:explicit', item_itunes_attrs['explicit'])
        
        if 'episode' in item_itunes_attrs:
            handler.addQuickElement('itunes:episode', item_itunes_attrs['episode'])
        
        if 'season' in item_itunes_attrs:
            handler.addQuickElement('itunes:season', item_itunes_attrs['season'])


class PodcastFeedView(View):
    """View to generate the podcast RSS feed."""
    
    def get(self, request):
        site = request.site
        
        # Basic feed setup
        feed = PodcastFeed(
            title="Into the Moss",
            link="https://intothemoss.com/",
            description="Into the Moss is a 14 minute drift through original music, soundscapes and liminal yarns, broadcast on London's Resonance 104.4 FM",
            language="en-us",
            author_name="Into the Moss",
            feed_url="https://intothemoss.com/feed.xml",
        )
        
        # Add episodes to the feed
        episodes = PodcastEpisodePage.objects.live().public().order_by('-publication_date')
        
        for episode in episodes:
            # Format duration as HH:MM:SS
            if episode.duration_in_seconds:
                minutes, seconds = divmod(episode.duration_in_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration = "00:14:00"  # Default 14 minutes
            
            # Get the episode cover image URL
            if episode.cover_image:
                image_url = request.build_absolute_uri(episode.cover_image.get_rendition('original').url)
            else:
                image_url = request.build_absolute_uri('/static/images/podcast-cover.jpg')
            
            # Add episode to feed
            feed.add_item(
                title=f"Episode {episode.episode_number}: {episode.title}",
                link=request.build_absolute_uri(episode.get_full_url()),
                description=str(episode.description),
                pubdate=episode.publication_date,
                unique_id=episode.guid if episode.guid else f"intothemoss-ep{episode.episode_number}",
                enclosure={
                    'url': request.build_absolute_uri(episode.audio_file.url),
                    'length': str(os.path.getsize(episode.audio_file.path)) if os.path.exists(episode.audio_file.path) else '0',
                    'mime_type': 'audio/mpeg',
                },
                itunes={
                    'duration': duration,
                    'summary': str(episode.description),
                    'image': image_url,
                    'explicit': 'true' if episode.explicit_content else 'false',
                    'episode': str(episode.episode_number),
                    'season': str(episode.season_number),
                },
            )
        
        # Generate and return the feed
        response = HttpResponse(content_type='application/rss+xml; charset=utf-8')
        feed.write(response, 'utf-8')
        return response
