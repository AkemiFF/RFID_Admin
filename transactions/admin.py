from django.contrib import admin
from .models import Transaction, Rechargement


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference_interne', 'carte', 'type_transaction', 'montant', 'statut', 'date_transaction']
    list_filter = ['type_transaction', 'statut', 'date_transaction']
    search_fields = ['reference_interne', 'reference_externe', 'merchant_nom']
    readonly_fields = ['id', 'date_transaction']


@admin.register(Rechargement)
class RechargementAdmin(admin.ModelAdmin):
    list_display = ['recu_numero', 'carte', 'montant_recharge', 'mode_paiement', 'statut_paiement', 'date_rechargement']
    list_filter = ['mode_paiement', 'statut_paiement', 'date_rechargement']
    search_fields = ['recu_numero', 'reference_paiement']
    readonly_fields = ['id', 'date_rechargement']
