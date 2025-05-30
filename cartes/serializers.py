from django.utils import timezone
from rest_framework import serializers

from .models import CarteRFID, HistoriqueStatutsCarte


class CarteRFIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarteRFID
        fields = '__all__'


class HistoriqueStatutsCarteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueStatutsCarte
        fields = '__all__'


class ClientCarteRFIDSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les cartes RFID côté client"""
    id = serializers.UUIDField(read_only=True)
    numero = serializers.CharField(source='numero_serie')
    type = serializers.CharField(source='type_carte')
    statut = serializers.CharField()
    solde = serializers.DecimalField(max_digits=15, decimal_places=2)
    dateCreation = serializers.DateTimeField(source='date_creation')
    dateExpiration = serializers.DateField(source='date_expiration')
    plafondJournalier = serializers.DecimalField(source='plafond_quotidien', max_digits=15, decimal_places=2)
    plafondMensuel = serializers.DecimalField(source='plafond_mensuel', max_digits=15, decimal_places=2)
    utiliseJournalier = serializers.SerializerMethodField()
    utiliseMensuel = serializers.SerializerMethodField()
    dernierUtilisation = serializers.DateTimeField(source='derniere_utilisation', required=False)
    nombreTransactions = serializers.IntegerField(source='nombre_transactions')
    fraisMensuels = serializers.SerializerMethodField()
    couleur = serializers.SerializerMethodField()
    nomPersonnalise = serializers.SerializerMethodField()

    class Meta:
        model = CarteRFID
        fields = [
            'id', 'numero', 'type', 'statut', 'solde', 'dateCreation', 'dateExpiration',
            'plafondJournalier', 'plafondMensuel', 'utiliseJournalier', 'utiliseMensuel',
            'dernierUtilisation', 'nombreTransactions', 'fraisMensuels', 'couleur', 'nomPersonnalise'
        ]

    def get_utiliseJournalier(self, obj):
        # Dans un système réel, nous calculerions le montant utilisé aujourd'hui
        # Pour cet exemple, nous retournons une valeur aléatoire
        import random
        return float(random.randint(0, int(obj.plafond_quotidien)))

    def get_utiliseMensuel(self, obj):
        # Dans un système réel, nous calculerions le montant utilisé ce mois-ci
        # Pour cet exemple, nous retournons une valeur aléatoire
        import random
        return float(random.randint(0, int(obj.plafond_mensuel)))

    def get_fraisMensuels(self, obj):
        # Frais mensuels en fonction du type de carte
        if obj.type_carte == 'STANDARD':
            return 5000
        elif obj.type_carte == 'PREMIUM':
            return 15000
        elif obj.type_carte == 'ENTREPRISE':
            return 25000
        return 0

    def get_couleur(self, obj):
        # Couleur en fonction du type de carte
        if obj.type_carte == 'STANDARD':
            return '#6B7280'  # Gris
        elif obj.type_carte == 'PREMIUM':
            return '#F59E0B'  # Ambre
        elif obj.type_carte == 'ENTREPRISE':
            return '#10B981'  # Vert émeraude
        return '#6B7280'  # Gris par défaut

    def get_nomPersonnalise(self, obj):
        # Dans un système réel, nous récupérerions le nom personnalisé
        # Pour cet exemple, nous retournons None
        return None


class CarteRFIDDetailSerializer(ClientCarteRFIDSerializer):
    """Sérialiseur pour les détails d'une carte RFID"""
    dateActivation = serializers.DateTimeField(source='date_activation', required=False)
    lieuEmission = serializers.CharField(source='lieu_emission')
    versionSecurite = serializers.CharField(source='version_securite')
    
    class Meta(ClientCarteRFIDSerializer.Meta):
        fields = ClientCarteRFIDSerializer.Meta.fields + [
            'dateActivation', 'lieuEmission', 'versionSecurite'
        ]


class CarteLimitsSerializer(serializers.Serializer):
    """Sérialiseur pour les limites d'une carte"""
    plafondJournalier = serializers.DecimalField(max_digits=15, decimal_places=2)
    plafondMensuel = serializers.DecimalField(max_digits=15, decimal_places=2)


class CarteSettingsSerializer(serializers.Serializer):
    """Sérialiseur pour les paramètres d'une carte"""
    notifications = serializers.DictField(child=serializers.BooleanField())
    securite = serializers.DictField(child=serializers.BooleanField())
    preferences = serializers.DictField(child=serializers.CharField())


class CarteStatisticsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques d'une carte"""
    totalTransactions = serializers.IntegerField()
    totalAmount = serializers.DecimalField(max_digits=15, decimal_places=2)
    averageTransaction = serializers.DecimalField(max_digits=15, decimal_places=2)
    topMerchants = serializers.ListField(child=serializers.DictField())
    dailyUsage = serializers.ListField(child=serializers.DictField())


class CarteRequestSerializer(serializers.Serializer):
    """Sérialiseur pour les demandes de carte"""
    type = serializers.ChoiceField(choices=['standard', 'premium', 'business'])
    motif = serializers.CharField()
    adresseLivraison = serializers.CharField()
    urgence = serializers.BooleanField(default=False)


class CartePINSerializer(serializers.Serializer):
    """Sérialiseur pour les opérations liées au PIN"""
    pin = serializers.CharField(min_length=4, max_length=6)
    currentPin = serializers.CharField(min_length=4, max_length=6, required=False)
    newPin = serializers.CharField(min_length=4, max_length=6, required=False)
