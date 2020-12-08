
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('worksheet.urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]
