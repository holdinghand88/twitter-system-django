from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse, HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from .decorators import twitter_login_required
from .models import TwitterAuthToken, TwitterUser,TwitterAccount
from .authorization import create_update_user_from_twitter, check_token_still_valid
from twitter_api.twitter_api import TwitterAPI
from django.views.generic import ListView, DetailView, View, TemplateView, CreateView
from django.views.generic.edit import UpdateView
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserCreateForm, ProfiledAuthenticationForm, UserUpdateForm
from django.contrib import messages

# Create your views here.
class LoginView(View):
    template_name = "registration/login.html"
    form_class = ProfiledAuthenticationForm
    
    def get_success_url(self):
        return reverse('authorization:index')
    
    def get(self, request, *args, **kwargs):
        
        context = {'form': self.form_class()}
        if self.request.user.is_authenticated:
            return render(request, 'home.html')
        else:
            return render(request,self.template_name,context)
        
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)                
                return HttpResponseRedirect(self.get_success_url())

        return render(request, self.template_name, {'form': form})

class Signup(View):
    redirect_authenticated_user = True
    form_class = UserCreateForm
    template_name = 'registration/signup.html'
    
    def get(self, request, *args, **kwargs):
        context = {'form': self.form_class()}
        return render(request, self.template_name, context)

def twitter_login(request):
    twitter_api = TwitterAPI()
    url, oauth_token, oauth_token_secret = twitter_api.twitter_login()
    if url is None or url == '':
        messages.add_message(request, messages.ERROR, 'Unable to login. Please try again.')
        return render(request, 'registration/error_page.html')
    else:
        twitter_auth_token = TwitterAuthToken.objects.filter(oauth_token=oauth_token).first()
        if twitter_auth_token is None:
            twitter_auth_token = TwitterAuthToken(oauth_token=oauth_token, oauth_token_secret=oauth_token_secret)
            twitter_auth_token.save()
        else:
            twitter_auth_token.oauth_token_secret = oauth_token_secret
            twitter_auth_token.save()
        return redirect(url)


def twitter_callback(request):
    if 'denied' in request.GET:
        messages.add_message(request, messages.ERROR, 'Unable to login or login canceled. Please try again.')
        return render(request, 'registration/error_page.html')
    twitter_api = TwitterAPI()
    oauth_verifier = request.GET.get('oauth_verifier')
    oauth_token = request.GET.get('oauth_token')
    twitter_auth_token = TwitterAuthToken.objects.filter(oauth_token=oauth_token).first()
    if twitter_auth_token is not None:
        access_token, access_token_secret = twitter_api.twitter_callback(oauth_verifier, oauth_token, twitter_auth_token.oauth_token_secret)
        if access_token is not None and access_token_secret is not None:
            twitter_auth_token.oauth_token = access_token
            twitter_auth_token.oauth_token_secret = access_token_secret
            twitter_auth_token.save()
            # Create user
            client = twitter_api.client_init(access_token, access_token_secret)
            info = twitter_api.get_me(client)
            if info is not None:
                twitter_user_new = TwitterUser(twitter_id=info[0]['id'], screen_name=info[0]['username'],
                                               name=info[0]['name'], profile_image_url=info[0]['profile_image_url'])
                twitter_user_new.twitter_oauth_token = twitter_auth_token
                user, twitter_user = create_update_user_from_twitter(twitter_user_new)
                if user is not None:
                    login(request, user)
                    return redirect('core:homepage')
            else:
                messages.add_message(request, messages.ERROR, 'Unable to get profile details. Please try again.')
                return render(request, 'registration/error_page.html')
        else:
            messages.add_message(request, messages.ERROR, 'Unable to get access token. Please try again.')
            return render(request, 'registration/error_page.html')
    else:
        messages.add_message(request, messages.ERROR, 'Unable to retrieve access token. Please try again.')
        return render(request, 'registration/error_page.html')

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'profile.html'

    def get_success_url(self):        
        return reverse('authorization:profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(ProfileUpdateView, self).get_context_data(**kwargs)
        if 'pw_form' not in context:
            context['pw_form'] = PasswordChangeForm(user=self.request.user)
        context['form'] = self.form_class(instance=self.get_object())
        print(context)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        ctxt = {} 

        if 'pw_form' in request.POST:
            print("Checking pw form")
            pw_form = PasswordChangeForm(user=request.user, data=request.POST)
            if pw_form.is_valid():
                print("pw_form is valid")
                messages.add_message(self.request, messages.SUCCESS, 'Password changed successfully.')
                pw_form.save()
                update_session_auth_hash(self.request, pw_form.user)                
            else:
                print(pw_form.errors)
                ctxt['pw_form'] = pw_form
        
        return render(request, self.template_name, self.get_context_data(**ctxt))

class TwitterAccountView(auth_views.LoginView):
    template_name = "twitteraccount.html"
    model = TwitterAccount
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super(TwitterAccountView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                context['accounts'] = TwitterAccount.objects.all()
            else:
                context['accounts'] = TwitterAccount.objects.filter(user=self.request.user)
        return context
        
def termview(request):
    template_name = "registration/termuse.html" 
    
    return render(request, template_name)

@login_required
@twitter_login_required
def index(request):
    return render(request, 'home.html')


@login_required
def twitter_logout(request):
    logout(request)
    return redirect('authorization:login')

@login_required
def logout_c(request):
    logout(request)
    return redirect('authorization:login')

@login_required
def change_user(request):
    email = request.POST.get('email')
    email_exists = User.objects.filter(email=email).exclude(id=request.user.id)
    if email_exists.exists():
        return JsonResponse({'success':False})
    else:
        lastname = request.POST.get('last_name')
        firstname = request.POST.get('first_name')
        user = request.user
        user.last_name = lastname
        user.first_name = firstname
        user.email = email
        user.save()
        
        return JsonResponse({'success':True})
