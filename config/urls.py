from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('authorization/', include(('authorization.urls', 'authorization'),namespace='authorization')),
    path('admin/', admin.site.urls),
    path('', include('core.urls'))
]
