from django.contrib import admin
from .models import ApiClient, ApiLog


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ['nom_client', 'client_id', 'type_client', 'niveau_acces', 'actif', 'date_creation']
    list_filter = ['type_client', 'niveau_acces', 'actif']
    search_fields = ['nom_client', 'client_id', 'organisation']
    readonly_fields = ['id', 'date_creation', 'nombre_requetes_total']


@admin.register(ApiLog)
class ApiLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'methode_http', 'endpoint', 'code_reponse', 'duree_traitement', 'date_requete']
    list_filter = ['methode_http', 'code_reponse', 'date_requete']
    search_fields = ['endpoint', 'trace_id']
    readonly_fields = ['id', 'date_requete']
    date_hierarchy = 'date_requete'
