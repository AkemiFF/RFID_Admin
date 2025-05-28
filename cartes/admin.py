from django.contrib import admin
from .models import CarteRFID, HistoriqueStatutsCarte


@admin.register(CarteRFID)
class CarteRFIDAdmin(admin.ModelAdmin):
    list_display = ['numero_serie', 'code_uid', 'statut', 'solde', 'date_emission']
    list_filter = ['statut', 'type_carte', 'date_emission']
    search_fields = ['numero_serie', 'code_uid']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(HistoriqueStatutsCarte)
class HistoriqueStatutsCarteAdmin(admin.ModelAdmin):
    list_display = ['carte', 'ancien_statut', 'nouveau_statut', 'date_changement']
    list_filter = ['ancien_statut', 'nouveau_statut', 'date_changement']
    readonly_fields = ['id', 'date_changement']
