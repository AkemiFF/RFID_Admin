from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Personne, Entreprise, Utilisateur
from .serializers import PersonneSerializer, EntrepriseSerializer, UtilisateurSerializer


class PersonneViewSet(viewsets.ModelViewSet):
    queryset = Personne.objects.all()
    serializer_class = PersonneSerializer
    permission_classes = [IsAuthenticated]


class EntrepriseViewSet(viewsets.ModelViewSet):
    queryset = Entreprise.objects.all()
    serializer_class = EntrepriseSerializer
    permission_classes = [IsAuthenticated]


class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]
