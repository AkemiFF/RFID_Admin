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
