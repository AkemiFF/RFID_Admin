from rest_framework import serializers
from .models import ParametreSysteme


class ParametreSystemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametreSysteme
        fields = '__all__'
