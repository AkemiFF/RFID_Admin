from rest_framework import serializers
from .models import DocumentIdentite


class DocumentIdentiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentIdentite
        fields = '__all__'
