from django.contrib import admin
from .models import ParametreSysteme


@admin.register(ParametreSysteme)
class ParametreSystemeAdmin(admin.ModelAdmin):
    list_display = ['cle', 'valeur', 'type_valeur', 'categorie', 'modifiable', 'date_modification']
    list_filter = ['type_valeur', 'categorie', 'modifiable', 'visible_interface']
    search_fields = ['cle', 'description']
    readonly_fields = ['id', 'date_creation', 'date_modification']
