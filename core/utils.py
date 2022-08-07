from tkinter import E
from django.shortcuts import render, redirect, get_object_or_404
from authorization.models import TwitterAuthToken, TwitterUser
from .models import keywords,NotificationSettings,LogoUserAction,AutoLikeSetting
from twitter_api.twitter_api import TwitterAPI
import time
import random
import datetime
import pytz
import json
import os

def autolike(user,hashtags):
    twitter_api = TwitterAPI()
    twitter_user = get_object_or_404(TwitterUser,user=user)
    twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
    client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
    hashtag = random.choice(hashtags)
    query = str(hashtag.keyword)
    max_results = 100
    
    search_tweets = twitter_api.search_recent_tweets(client,query,max_results)
    tweet_id = random.choice(search_tweets[0]).id
    
    print(tweet_id)
    
    try:
        client.like(tweet_id=tweet_id,user_auth=True)
        return tweet_id
    except:
        pass
        return ''
    
    
def autoretweet(user,hashtags):
    twitter_api = TwitterAPI()
    twitter_user = get_object_or_404(TwitterUser,user=user)
    twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
    client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
    hashtag = random.choice(hashtags)
    query = str(hashtag.keyword)
    max_results = 100
    
    search_tweets = twitter_api.search_recent_tweets(client,query,max_results)
    tweet_id = random.choice(search_tweets[0]).id
    print(tweet_id)
    
    try:
        client.retweet(tweet_id=tweet_id,user_auth=True)
        return tweet_id
    except:
        pass
        return ''

def autofollow(user,hashtags):
    twitter_api = TwitterAPI()
    twitter_user = get_object_or_404(TwitterUser,user=user)
    twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
    client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
    hashtag = random.choice(hashtags)
    query = str(hashtag.keyword)
    max_results = 100
    try:
        search_tweets = twitter_api.search_recent_tweets(client,query,max_results)
        tweet_id = random.choice(search_tweets[0]).id
        #print(tweet_id)
        tweet = client.get_tweet(tweet_id,user_auth=True,expansions=['author_id'],user_fields=['id'])
        user_id = tweet[1]['users'][0].id
        try:
            client.follow_user(target_user_id=user_id,user_auth=True)
            print(user_id)
            return user_id
        except:
            return ''
    except:
        pass
        return ''