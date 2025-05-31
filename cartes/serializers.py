from rest_framework import serializers
from .models import CarteRFID, HistoriqueStatutsCarte
from shared.serializers import PersonneSerializer, EntrepriseSerializer


class CarteRFIDSerializer(serializers.ModelSerializer):
    personne = PersonneSerializer(read_only=True)
    entreprise = EntrepriseSerializer(read_only=True)
    class Meta:
        model = CarteRFID
        fields = '__all__'


class HistoriqueStatutsCarteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueStatutsCarte
        fields = '__all__'
