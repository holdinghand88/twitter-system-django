from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404,reverse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse,JsonResponse
from requests import request
from twitter_api.twitter_api import TwitterAPI
from authorization.models import TwitterAuthToken, TwitterUser
from .models import keywords,DraftTweets,AssetModel,NotificationSettings,LogoUserAction,AutoLikeSetting,PaymentHistory
from .forms import AddKeywordForm,NotificationSettingForm,DraftForm,DraftFileForm,PostingTimeForm
from .utils import autolike,autoretweet,autofollow
import time
import random
import datetime
import pytz
import json
import os
import threading
import stripe
from config.settings import STRIPE_PUBLISHABLE_KEY,STRIPE_SECRET_KEY,STRIPE_ENDPOINT_SECRET

class HomeView(auth_views.LoginView):
    template_name = "home.html"    
    
    def get(self, request, *args, **kwargs):      
        context = self.get_context_data()
        if self.request.user.is_authenticated:            
            
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
        
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        twitter_api = TwitterAPI()
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                context['users'] = User.objects.all().order_by('-date_joined')
            else:
                twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
                twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
                client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
                
                info = twitter_api.get_me(client)
                #print(self.request.user.email)                             
                context['followers_count'] = info[0]['public_metrics']['followers_count']            
                context['following_count'] = info[0]['public_metrics']['following_count']
                context['logs'] = LogoUserAction.objects.filter(user=self.request.user).order_by('-pub_date')
                liked_tweets = twitter_api.get_liked_tweets(twitter_user.twitter_id,client)
                #print(liked_tweets[3]['result_count'])
                context['liked_tweets'] = liked_tweets[3]['result_count']
                max_result = 5
                _tweets = twitter_api.get_users_tweets(twitter_user.twitter_id,client,max_result)                
                context['tweets'] = _tweets[0]
                context['tweets_count'] = info[0]['public_metrics']['tweet_count']
                following_info = twitter_api.get_users_following(twitter_user.twitter_id,client,10)
                context['followings'] = following_info[0]
                #print(context['followings'])
            
        return context

class GetHashTag(auth_views.LoginView):
    model = keywords
    paginate_by = 10
    template_name = "hashtag.html"

    def get(self, request, *args, **kwargs):
        
        if self.request.user.is_authenticated:
            context = self.get_context_data()
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super(GetHashTag, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['hashtags'] = keywords.objects.filter(user=self.request.user)
        return context
    
    def post(self, request, *args, **kwargs):
        form = AddKeywordForm(request.POST)
        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            if keyword is not None:
                hashtag = keywords()
                hashtag.keyword = keyword
                hashtag.user = request.user
                hashtag.save()
                return redirect('core:hashtag')
            else:
                return redirect('core:hashtag')
        else:
            return redirect('core:hashtag')
        
def HashTagDelete(request,pk):
    hashtag = keywords.objects.filter(id=pk)
    hashtag.delete()
    return redirect("core:hashtag")

               
class AutoLikeView(auth_views.LoginView):
    model = keywords
    template_name = "autolike.html"
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()   
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_context_data(self, **kwargs):
        twitter_api = TwitterAPI()
        context = super(AutoLikeView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                context['hashtags'] = keywords.objects.filter(user=self.request.user)
            except:
                context['hashtags'] = []
            try:
                context['likesettings'] = AutoLikeSetting.objects.get(user=self.request.user,action_code=1)
            except:
                context['likesettings'] = []
            
            context['logs'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=1).order_by('-pub_date')
            twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
            twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
            client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            info = twitter_api.get_me(client)
            liked_tweets = twitter_api.get_liked_tweets(twitter_user.twitter_id,client)            
            context['liked_count'] = info[0]['public_metrics']['listed_count'] 
            context['liked_tweets'] = liked_tweets[0]
        return context

def save_autolike_setting(request):
    try:
        action_code =  int(request.POST.get('action_code'))
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')
        frequency = request.POST.get('frequency')        
        end_date_str = end_date + ' ' + end_time        
        end_datetime_object = datetime.datetime.fromisoformat(end_date_str).astimezone(pytz.timezone('Asia/Tokyo'))
        now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Tokyo'))
        if end_datetime_object < now:
            
            resp = HttpResponse(f'{{"message": "failed"}}')
            resp.status_code = 400
            resp.content_type = "application/json"
            return resp
        if frequency == '':
            frequency=1
        
        try:
            likesetting = AutoLikeSetting.objects.get(user=request.user, action_code=action_code)
        except:
            likesetting = AutoLikeSetting()
        likesetting.user = request.user
        likesetting.end_time = end_datetime_object
        likesetting.frequency = frequency
        likesetting.action_code = action_code
        likesetting.status = False
        likesetting.save()
        
        resp = HttpResponse(f'{{"message": "Success"}}')
        resp.status_code = 200
        resp.content_type = "application/json"
        return resp
    except:
        resp = HttpResponse(f'{{"message": "failed"}}')
        resp.status_code = 400
        resp.content_type = "application/json"
        return resp

def autolikestart(request):
    try:
        try:
            action_code =  int(request.POST.get('action_code'))
            likesetting = AutoLikeSetting.objects.get(user=request.user, action_code=action_code)
            hashtags = keywords.objects.filter(user=request.user)
        except:
            resp = HttpResponse(f'{{"message": "failed"}}')
            resp.status_code = 400
            resp.content_type = "application/json"
            return resp
        if len(hashtags) > 0:
            
            likesetting.status = True
            likesetting.save()
            time.sleep(1)
            def run():
                while True:
                    now = datetime.datetime.now().astimezone(pytz.timezone('Asia/Tokyo'))
                    likesetting = AutoLikeSetting.objects.get(user=request.user, action_code=action_code)
                    frequency = likesetting.frequency
                    max_frequency = 300
                    if frequency > max_frequency:
                        frequency = max_frequency
                    frequency_time = int(24*3600/frequency)
                    #### frequency 当り回収
                    end_time = likesetting.end_time
                    if now > end_time:
                        break
                    if likesetting.status:
                        try:                            
                            if action_code == 1:
                                
                                print(str(request.user.id)+ '===' + str(now) + '===>>いいね')
                                tweet_id = autolike(request.user,hashtags)
                                if tweet_id != '':
                                    LogoUserAction.objects.create(user=request.user, action_code=action_code, target_id=tweet_id, action_param='自動いいね。')
                                time.sleep(35)
                            elif action_code == 2:
                                print(str(request.user.id)+ '===' + str(now) + '===>>リツイート')
                                tweet_id = autoretweet(request.user,hashtags)
                                if tweet_id != '':
                                    LogoUserAction.objects.create(user=request.user, action_code=action_code, target_id=tweet_id, action_param='自動リツイート。')
                                time.sleep(35)
                            elif action_code == 3:
                                print(str(request.user.id)+ '===' + str(now) + '===>>フォロー')
                                user_id = autofollow(request.user,hashtags)
                                if user_id != '':
                                    LogoUserAction.objects.create(user=request.user, action_code=action_code, target_id=user_id, action_param='自動フォロー。')
                                time.sleep(30)
                            #time.sleep(random.randint(int(frequency_time/2), int(frequency_time*2)))
                        except:
                            break
                    else:
                        break
            thread = threading.Thread(target=run)
            thread.start()
            if action_code == 1:
                LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動いいねをスタート。')
            elif action_code == 2:
                LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動リツイートをスタート。')
            elif action_code == 3:
                LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動フォローをスタート。')
            resp = HttpResponse(f'{{"message": "Succcess..."}}')
            resp.status_code = 200
            resp.content_type = "application/json"
            return resp
        else:
            resp = HttpResponse(f'{{"message": "failed"}}')
            resp.status_code = 400
            resp.content_type = "application/json"
            return resp          
        
    except:
        resp = HttpResponse(f'{{"message": "failed"}}')
        resp.status_code = 400
        resp.content_type = "application/json"
        return resp

def autolikestop(request):
    try:
        action_code =  int(request.POST.get('action_code'))
        likesetting = AutoLikeSetting.objects.get(user=request.user, action_code=action_code)
        likesetting.status = False
        likesetting.save()        
        
        if action_code == 1:
            LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動いいねを中止。')
        elif action_code == 2:
            LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動リツイートを中止。')
        elif action_code == 3:
            LogoUserAction.objects.create(user=request.user, action_code=action_code, action_param='自動フォローを中止。')
        
        resp = HttpResponse(f'{{"message": "Succcess..."}}')
        resp.status_code = 200
        resp.content_type = "application/json"
        return resp
    except:
        resp = HttpResponse(f'{{"message": "failed"}}')
        resp.status_code = 400
        resp.content_type = "application/json"
        return resp        
        
class NotificationSettingAPI(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        n_settings = NotificationSettings.objects.get(user=request.user)
        context = {
            'notification': n_settings
        }
        return render(self.request, "notificationsettings.html", context)
    
    def post(self, request, *args, **kwargs):
        form = NotificationSettingForm(self.request.POST)
        if form.is_valid():
            retrieval = form.cleaned_data.get('retrieval')
            daily = form.cleaned_data.get('daily')
            weekly = form.cleaned_data.get('weekly')
            notices = form.cleaned_data.get('notices')            
            key_monitor = form.cleaned_data.get('key_monitor')
            monitor_frequency = form.cleaned_data.get('monitor_frequency')
            try:
                n_setting_obj = NotificationSettings.objects.get(user=request.user)
                n_setting_obj.retrieval = retrieval
                n_setting_obj.daily = daily
                n_setting_obj.weekly = weekly
                n_setting_obj.notices = notices                
                n_setting_obj.key_monitor = key_monitor
                n_setting_obj.monitor_frequency = monitor_frequency
                n_setting_obj.save()
                
            except ObjectDoesNotExist:
                messages.warning(self.request, "You do not have an active order")
                return redirect("/")
            return redirect("/")
        else:
            messages.warning(self.request, "Invalid Form")
            return redirect("/")
        
class DraftTweetAPI(LoginRequiredMixin, View):
    model = DraftTweets
    form_class = DraftForm
    template_name = "drafttweets.html"
    success_url = reverse_lazy('core:drafttweet')
    
    def get(self, request, *args, **kwargs):
        drafttweets = DraftTweets.objects.get(user=request.user)
        context = {
            'drafttweets': drafttweets
        }
        return render(self.request, "drafttweets.html", context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        file_form = DraftFileForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            drafttweet = form.save()
            if request.FILES:
                for file in request.FILES:
                    file = request.FILES[file]
                    draft_file = AssetModel(asset_file=file)
                    draft_file.drafttweet = drafttweet
                    draft_file.save()
                resp = HttpResponse(f'{{"message": "Uploaded successfully...", "id": "{drafttweet}"}}')
                resp.status_code = 200
                resp.content_type = "application/json"
                return resp
            else:
                return redirect("core:drafttweet")
        else:
            messages.warning(self.request, "Invalid Form")
            return redirect("/")
        

class HistoryLikeView(auth_views.LoginView):
    template_name = "history.html"
    model = LogoUserAction
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
        
    def get_context_data(self, **kwargs):
        context = super(HistoryLikeView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:            
            context['histories'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=1).order_by('-pub_date')            
        return context
    
class HistoryRetweetView(auth_views.LoginView):
    template_name = "history.html"
    model = LogoUserAction
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
        
    def get_context_data(self, **kwargs):
        context = super(HistoryRetweetView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:            
            context['histories'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=2).order_by('-pub_date')            
        return context
    
class HistoryFollowView(auth_views.LoginView):
    template_name = "history.html"
    model = LogoUserAction
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
        
    def get_context_data(self, **kwargs):
        context = super(HistoryFollowView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:            
            context['histories'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=3).order_by('-pub_date')            
        return context

class HistoryAllView(auth_views.LoginView):
    template_name = "history.html"
    model = LogoUserAction
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
        
    def get_context_data(self, **kwargs):
        context = super(HistoryAllView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:            
            context['histories'] = LogoUserAction.objects.filter(user=self.request.user).order_by('-pub_date')            
        return context
    
    
############ ReTweet #########
class AutoRetweetView(auth_views.LoginView):
    model = keywords
    template_name = "autoretweet.html"
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()   
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_context_data(self, **kwargs):
        twitter_api = TwitterAPI()
        context = super(AutoRetweetView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                context['hashtags'] = keywords.objects.filter(user=self.request.user)
            except:
                context['hashtags'] = []
            try:
                context['likesettings'] = AutoLikeSetting.objects.get(user=self.request.user,action_code=2)
            except:
                context['likesettings'] = []
            
            context['logs'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=2).order_by('-pub_date')
            twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
            twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
            client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            info = twitter_api.get_me(client)
            
            max_result = 10
            end_time = datetime.datetime.now()
            start_time = datetime.datetime.now() - datetime.timedelta(days=30)            
            tweets = twitter_api.get_users_tweets(twitter_user.twitter_id,client,max_result,end_time,start_time)
            
            context['retweet_count'] = info[0]['public_metrics']['tweet_count']
            context['retweet_tweets'] = tweets[0]
        return context
    
    
############ Follow #############
class AutoFollowView(auth_views.LoginView):
    model = keywords
    template_name = "autofollow.html"
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()   
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_context_data(self, **kwargs):
        twitter_api = TwitterAPI()
        context = super(AutoFollowView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                context['hashtags'] = keywords.objects.filter(user=self.request.user)
            except:
                context['hashtags'] = []
            try:
                context['likesettings'] = AutoLikeSetting.objects.get(user=self.request.user,action_code=3)
            except:
                context['likesettings'] = []
            
            context['logs'] = LogoUserAction.objects.filter(user=self.request.user).filter(action_code=3).order_by('-pub_date')
            twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
            twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
            client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            info = twitter_api.get_me(client)
            
            following_info = twitter_api.get_users_following(twitter_user.twitter_id,client,100)
            context['following_count'] = info[0]['public_metrics']['following_count']
            context['followings'] = following_info[0]
        return context
    
################## Following and Follower ###################
class FollowView(auth_views.LoginView):
    model = keywords
    template_name = "following.html"
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()   
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_context_data(self, **kwargs):
        twitter_api = TwitterAPI()
        context = super(FollowView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            
            twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
            twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
            client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            info = twitter_api.get_me(client)
            following_info = twitter_api.get_users_following(twitter_user.twitter_id,client,1000)
            context['following_count'] = info[0]['public_metrics']['following_count']
            context['followings'] = following_info[0]
        return context
    
class FollowerView(auth_views.LoginView):
    model = keywords
    template_name = "follower.html"
    
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated: 
            context = self.get_context_data()   
            return render(request, self.template_name, context)
        else:
            return redirect('authorization:login')
    
    def get_context_data(self, **kwargs):
        twitter_api = TwitterAPI()
        context = super(FollowerView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            
            twitter_user = get_object_or_404(TwitterUser,user=self.request.user)
            twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
            client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            #api = twitter_api.api_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
            info = twitter_api.get_me(client)
                                    
            context['followers_count'] = info[0]['public_metrics']['followers_count']            
            
            following_info = twitter_api.get_users_following_ids(twitter_user.twitter_id,client,1000)
            #following_l = api.get_friend_ids(tuser_id=twitter_user.twitter_id,count=5000)
            followers_info = twitter_api.get_users_followers(twitter_user.twitter_id,client,1000)                  
            following_ids = []
            if following_info[0] is not None:
                for following in following_info[0]:
                    following_ids.append(following.id)
            context['followings'] = following_ids
            context['followers'] = followers_info[0]
            #print(following_l)     
        return context
    
def follow(request,pk):
    twitter_api = TwitterAPI()
    twitter_user = get_object_or_404(TwitterUser,user=request.user)
    twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
    client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
    user_id = pk
    client.follow_user(target_user_id=user_id,user_auth=True)
    return redirect(reverse("core:follower"))

def unfollow(request,pk):
    twitter_api = TwitterAPI()
    twitter_user = get_object_or_404(TwitterUser,user=request.user)
    twitter_auth_token = get_object_or_404(TwitterAuthToken, id=twitter_user.twitter_oauth_token.id)
    client = twitter_api.client_init(twitter_auth_token.oauth_token, twitter_auth_token.oauth_token_secret)
    user_id = pk
    print(user_id)
    client.unfollow_user(target_user_id=user_id,user_auth=True)
    return redirect(reverse("core:following"))


##################=======  プラン ===========##########
def payment(request):
    context = {}
    try:
        plan2 = PaymentHistory.objects.filter(user=request.user, storage=2).first()
        if len(plan2) > 0:
            context['plan2'] = 'purchased'
        else:
            context['plan2'] = ''
    except:
        context['plan2'] = ''
    
    return render(request, 'payment/payment.html', context)

@login_required
def payment_history(request):
    payment_history = PaymentHistory.objects.filter(user=request.user)
    return render(request, 'payment/payment_history.html', context={'payment_history':payment_history})

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        plan_id = request.GET.get('plan_id')
        user = request.user
        name = ''
        if plan_id=='1':
            name = 'Free'
            price = 0
            user = request.user            
            #user.profile.save()
            user.save()
            payment = PaymentHistory()
            payment.user = user
            payment.storage = 0
            payment.price = 0
            payment.save()
            return JsonResponse({'success':True})
        if plan_id=='2':
            name = '月'
            price = 2980
        
        #domain_url = 'http://127.0.0.1:8003/'
        domain_url = request.scheme+'://'+request.META['HTTP_HOST']+'/'
        if request.user.email == '':
            messages.add_message(request, messages.SUCCESS, 'メールアドレスをご記入ください！')
            email = 'example@domain.com'
            return JsonResponse({'email': 'error'})
        else:
            email = request.user.email
        print(request.user.email)
        stripe.api_key = STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}&plan_id='+plan_id,
                cancel_url=domain_url + 'payment',
                payment_method_types=['card'],
                customer_email=email,
                mode='payment',
                locale='ja',
                line_items=[
                    {
                        'name': name,
                        'quantity': 1,
                        'currency': 'JPY',
                        'amount': int(price),
                    }
                ],
                metadata={'plan_id':plan_id},
                client_reference_id = request.user.id
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = STRIPE_SECRET_KEY
    endpoint_secret = STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    print(event)
    if event['type'] == 'checkout.session.completed':

        data = event['data']['object']
        user_id = data['client_reference_id']
        user = User.objects.get(id=user_id)
        plan_id = int(data['metadata']['plan_id'])

        if int(plan_id) == 2:
            print("Payment Success!")
            payment = PaymentHistory()
            payment.user = user
            payment.storage = 2
            payment.price = 500
            payment.save()


    return HttpResponse(status=200)

class SuccessView(TemplateView):
    template_name = 'payment/payment_success.html'

    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get('plan_id')
        
        return render(request,self.template_name)

class CancelledView(TemplateView):
    template_name = 'payment/payment_cancelled.html'