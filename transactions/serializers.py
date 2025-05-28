from rest_framework import serializers
from .models import Transaction, Rechargement


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class RechargementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rechargement
        fields = '__all__'
