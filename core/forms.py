from django import forms
from .models import DraftTweets,AssetModel

class AddKeywordForm(forms.Form):
    keyword = forms.CharField(required=True)
    action_code = forms.IntegerField(required=True)
    
class NotificationSettingForm(forms.Form):
    retrieval = forms.BooleanField(required=True)
    daily = forms.BooleanField(required=True)
    weekly = forms.BooleanField(required=True)
    notices = forms.BooleanField(required=True)
    scheduled_empty = forms.BooleanField(required=True)
    key_monitor = forms.BooleanField(required=True)
    monitor_frequency = forms.IntegerField(required=True)
    
class DraftForm(forms.ModelForm):
    class Meta:
        model = DraftTweets
        fields = ['description']
        
class DraftFileForm(forms.ModelForm):
    class Meta:
        model = AssetModel
        fields = ['asset_file']
        
class PostingTimeForm(forms.Form):
    element = forms.CharField(required=True)
    timefield = forms.TimeField(required=True)