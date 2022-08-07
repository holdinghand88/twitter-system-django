from django.contrib import admin
from authorization.models import TwitterUser,TwitterAuthToken

admin.site.register(TwitterUser)
admin.site.register(TwitterAuthToken)
