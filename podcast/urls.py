from django.urls import path
from .views import PodcastFeedView

urlpatterns = [
    path('feed.xml', PodcastFeedView.as_view(), name='podcast_feed'),
]