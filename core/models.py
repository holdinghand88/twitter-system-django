from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from authorization.models import TwitterUser,TwitterAuthToken
import datetime
import pytz

class UserPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    column = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    sort_order = models.IntegerField()
    table = models.CharField(max_length=255)
    option = models.CharField(max_length=255)

class keywords(models.Model):
    """action_code: 
    1: autolike
    2: autoretweet
    3: autofollow    
    """
    keyword = models.CharField(max_length=256)
    action_code = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.keyword

class DraftTweets(models.Model):
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(_("Date added"),editable=False, auto_now_add=True)
    
    def __str__(self):
        return f"{self.twitter_id.name}"
    
class AssetModel(models.Model):
    drafttweet = models.ForeignKey(DraftTweets,on_delete=models.CASCADE)
    asset_file = models.FileField()
    
class NotificationSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    retrieval = models.BooleanField(default=False)
    daily = models.BooleanField(default=False)
    weekly = models.BooleanField(default=False)
    notices = models.BooleanField(default=False)
    scheduled_empty = models.BooleanField(default=False)
    key_monitor = models.BooleanField(default=True)
    monitor_frequency = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    
class PaymentHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    storage = models.IntegerField()
    price = models.FloatField(default=0)
    
class LogoUserAction(models.Model):
    """action_code: 
    1: autolike
    2: autoretweet
    3: autofollow    
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_param = models.CharField(_("param"), max_length=512, blank=True,null=True)
    action_code = models.IntegerField(default=0)
    target_id = models.CharField(max_length=512, blank=True,null=True)
    pub_date = models.DateTimeField(_("Date added"),editable=False, auto_now_add=True)
    
class AutoLikeSetting(models.Model):
    action_code = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    frequency = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1)])
    status = models.BooleanField(default=False)
    end_time = models.DateTimeField()

    
def model_receiver(sender, instance, created, *args, **kwargs):
    if created:
        #twitter_oauth_token = TwitterAuthToken.objects.create()
        #twitter = TwitterUser.objects.create(user=instance,twitter_oauth_token=twitter_oauth_token)
        notification_settings = NotificationSettings.objects.create(user=instance)
        
post_save.connect(model_receiver, sender=User)