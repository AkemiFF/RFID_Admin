"""rfid_system URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/identites/', include('identites.urls')),
    path('api/cartes/', include('cartes.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/logs/', include('logs.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/parametres/', include('parametres.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
