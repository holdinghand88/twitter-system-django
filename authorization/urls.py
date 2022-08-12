from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import ProfiledAuthenticationForm

app_name = "authorization"

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(form_class=ProfiledAuthenticationForm, redirect_authenticated_user=True), name="login"),
    path('singup/', views.Signup.as_view(), name="signup"),
    path('twitter_login/', views.twitter_login, name='twitter_login'),
    path('twitter_callback/', views.twitter_callback, name='twitter_callback'),
    path('twitter_logout/', views.twitter_logout, name='twitter_logout'),
    path('logout/',views.logout_c,name='logout'),
    path('profile/', views.ProfileUpdateView.as_view(), name="profile"),
    path('change_user/', views.change_user, name="change_user"),
    path('twitteraccount/', views.TwitterAccountView.as_view(), name="twitteraccount"),
    path('termofuse/', views.termview, name="termuse"),
]