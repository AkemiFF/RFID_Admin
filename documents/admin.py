from django.contrib import admin
from .models import DocumentIdentite


@admin.register(DocumentIdentite)
class DocumentIdentiteAdmin(admin.ModelAdmin):
    list_display = ['nom_fichier', 'type_document', 'statut_verification', 'date_upload']
    list_filter = ['type_document', 'statut_verification', 'niveau_confidentialite']
    search_fields = ['nom_fichier', 'hash_fichier']
    readonly_fields = ['id', 'date_upload', 'hash_fichier', 'taille_fichier']
