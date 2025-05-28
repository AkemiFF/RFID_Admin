from django.contrib import admin
from .models import LogSysteme


@admin.register(LogSysteme)
class LogSystemeAdmin(admin.ModelAdmin):
    list_display = ['niveau', 'action', 'module', 'utilisateur', 'date_creation']
    list_filter = ['niveau', 'action', 'module', 'date_creation']
    search_fields = ['action', 'message', 'trace_id']
    readonly_fields = ['id', 'date_creation']
    date_hierarchy = 'date_creation'
