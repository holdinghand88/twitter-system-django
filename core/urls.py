from django.urls import path

from .views import *

app_name = 'core'

urlpatterns = [
     
     path('',HomeView.as_view(), name="homepage"),
     path('hashtag/',GetHashTag.as_view(), name="hashtag"),
     path('hashtag/<int:pk>/delete',HashTagDelete, name="hashtagdelete"),
     
     ## BOT
     path('autolike/',AutoLikeView.as_view(), name="autolike"),
     path('autolike/start',autolikestart, name="autolikestart"),
     path('autolike/stop',autolikestop, name="autolikestop"),
     path('autolike/setting',save_autolike_setting, name="autolikesetting"),
     path('autoretweet/',AutoRetweetView.as_view(), name="autoretweet"),
     path('autofollow/',AutoFollowView.as_view(), name="autofollow"),
     
     ### History
     path('history/all',HistoryAllView.as_view(), name="historyall"),
     path('history/like',HistoryLikeView.as_view(), name="historylike"),
     path('history/retweet',HistoryRetweetView.as_view(), name="historyretweet"),
     path('history/follow',HistoryFollowView.as_view(), name="historyfollow"),
     
]
