from django.urls import path
from .views import PodcastFeedView, random_episode

urlpatterns = [
    path('feed.xml', PodcastFeedView.as_view(), name='podcast_feed'),
    path('random', random_episode, name='random_episode'),
]