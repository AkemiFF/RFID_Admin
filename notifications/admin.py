from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'destinataire', 'type_notification', 'canal', 'statut', 'date_creation']
    list_filter = ['type_notification', 'canal', 'statut', 'priorite']
    search_fields = ['titre', 'message', 'destinataire__username']
    readonly_fields = ['id', 'date_creation']
    date_hierarchy = 'date_creation'
