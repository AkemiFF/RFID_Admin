from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CarteRFID, HistoriqueStatutsCarte
from .serializers import CarteRFIDSerializer, HistoriqueStatutsCarteSerializer


class CarteRFIDViewSet(viewsets.ModelViewSet):
    queryset = CarteRFID.objects.all()
    serializer_class = CarteRFIDSerializer
    permission_classes = [IsAuthenticated]


class HistoriqueStatutsCarteViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueStatutsCarte.objects.all()
    serializer_class = HistoriqueStatutsCarteSerializer
    permission_classes = [IsAuthenticated]
