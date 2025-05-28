from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import LogSysteme
from .serializers import LogSystemeSerializer


class LogSystemeViewSet(viewsets.ModelViewSet):
    queryset = LogSysteme.objects.all()
    serializer_class = LogSystemeSerializer
    permission_classes = [IsAuthenticated]
