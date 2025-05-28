from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ParametreSysteme
from .serializers import ParametreSystemeSerializer


class ParametreSystemeViewSet(viewsets.ModelViewSet):
    queryset = ParametreSysteme.objects.all()
    serializer_class = ParametreSystemeSerializer
    permission_classes = [IsAuthenticated]
