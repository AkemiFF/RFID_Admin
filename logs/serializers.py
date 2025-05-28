from rest_framework import serializers
from .models import LogSysteme


class LogSystemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSysteme
        fields = '__all__'
