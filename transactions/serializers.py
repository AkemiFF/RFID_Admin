from rest_framework import serializers

from .models import Rechargement, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class RechargementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rechargement
        fields = '__all__'


class TransactionDetailSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_transaction_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    carte_numero = serializers.CharField(source='carte.numero_carte', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference_interne', 'reference_externe',
            'type_transaction', 'type_display',
            'statut', 'statut_display',
            'montant', 'frais_transaction', 'devise',
            'solde_avant', 'solde_apres',
            'merchant_id', 'merchant_nom', 'terminal_id',
            'description', 'categorie', 'localisation',
            'date_transaction', 'date_validation',
            'carte_numero', 'coordonnees_gps'
        ]
