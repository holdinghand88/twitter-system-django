from django.contrib import admin
from authorization.models import TwitterUser,TwitterAuthToken
from .models import AutoLikeSetting,LogoUserAction,keywords,PaymentHistory


class keywordsAdmin(admin.ModelAdmin):
    list_display = ('keyword','user')
    search_fields = ['keyword']
    
class AutoLikeSettingAdmin(admin.ModelAdmin):
    list_display = ('action_code','user','frequency','status','end_time')
    search_fields = ['action_code']

admin.site.register(TwitterUser)
admin.site.register(TwitterAuthToken)
admin.site.register(PaymentHistory)
admin.site.register(LogoUserAction)
admin.site.register(keywords, keywordsAdmin)
admin.site.register(AutoLikeSetting, AutoLikeSettingAdmin)


