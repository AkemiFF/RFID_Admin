from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from .models import Personne, Entreprise, Utilisateur
from .serializers import *
from cartes.serializers import CarteRFIDSerializer
from cartes.models import CarteRFID
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class PersonneViewSet(viewsets.ModelViewSet):
    queryset = Personne.objects.all()
    serializer_class = PersonneSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Données reçues pour création personne: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            personne = serializer.save()
            
            utilisateur = personne.utilisateur_set.first()
            if utilisateur:
                logger.info(f"Utilisateur créé avec succès: {utilisateur.username}")
            else:
                logger.warning(f"Aucun utilisateur créé pour la personne {personne.id}")
            
            response_data = serializer.data
            if utilisateur:
                response_data['utilisateur_info'] = UtilisateurSerializer(utilisateur).data
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            return Response({"error": "Validation failed", "details": e.detail}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error creating personne: {str(e)}")
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='assign-cartes', permission_classes=[IsAuthenticated])
    def assign_cartes(self, request):
        personne_id = request.data.get('personne_id')
        carte_ids = request.data.get('carte_ids', [])

        logger.info(f"Tentative d'assignation de cartes - Personne: {personne_id}, Cartes: {carte_ids}")

        if not personne_id or not carte_ids:
            return Response(
                {"error": "personne_id et carte_ids sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            personne = Personne.objects.get(id=personne_id)
        except Personne.DoesNotExist:
            return Response({"error": "Personne non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        assigned_cards_info = []
        errors = []

        for carte_id in carte_ids:
            try:
                carte = CarteRFID.objects.get(
                    id=carte_id, 
                    personne__isnull=True, 
                    entreprise__isnull=True
                )
                
                logger.info(f"Carte trouvée: {carte.id}, statut actuel: {carte.statut}")
                
                carte.personne = personne
                carte.statut = 'ACTIVE'
                carte.date_activation = timezone.now()
                carte.save()
                
                logger.info(f"Carte {carte.id} assignée avec succès à la personne {personne.id}")
                assigned_cards_info.append(CarteRFIDSerializer(carte).data)
                
            except CarteRFID.DoesNotExist:
                error_msg = f"Carte RFID {carte_id} non trouvée ou déjà assignée."
                logger.warning(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Erreur lors de l'assignation de la carte {carte_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            return Response({
                "message": "Certaines cartes ont été assignées, mais des erreurs sont survenues.",
                "assigned_cards": assigned_cards_info,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS if assigned_cards_info else status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Cartes assignées avec succès.",
            "assigned_cards": assigned_cards_info
        }, status=status.HTTP_200_OK)


class EntrepriseViewSet(viewsets.ModelViewSet):
    queryset = Entreprise.objects.all()
    serializer_class = EntrepriseSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            # Log des données reçues pour debug
            logger.info(f"Données reçues pour création entreprise: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            entreprise = serializer.save()
            
            # Vérifier si un utilisateur a été créé
            utilisateur = entreprise.utilisateur_set.first()
            if utilisateur:
                logger.info(f"Utilisateur créé avec succès: {utilisateur.username}")
            else:
                logger.warning(f"Aucun utilisateur créé pour l'entreprise {entreprise.id}")
            
            # Préparer la réponse avec les informations utilisateur
            response_data = serializer.data
            if utilisateur:
                response_data['utilisateur_info'] = UtilisateurSerializer(utilisateur).data
            
            headers = self.get_success_headers(response_data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {e.detail}")
            return Response({"error": "Validation failed", "details": e.detail}, 
                          status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error creating entreprise: {str(e)}")
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='assign-cartes', permission_classes=[IsAuthenticated])
    def assign_cartes(self, request):
        entreprise_id = request.data.get('entreprise_id')
        carte_ids = request.data.get('carte_ids', [])

        logger.info(f"Tentative d'assignation de cartes - Entreprise: {entreprise_id}, Cartes: {carte_ids}")

        if not entreprise_id or not carte_ids:
            return Response(
                {"error": "entreprise_id et carte_ids sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            entreprise = Entreprise.objects.get(id=entreprise_id)
            logger.info(f"Entreprise trouvée: {entreprise.raison_sociale}")
        except Entreprise.DoesNotExist:
            return Response({"error": "Entreprise non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        assigned_cards_info = []
        errors = []

        for carte_id in carte_ids:
            try:
                carte = CarteRFID.objects.get(
                    id=carte_id, 
                    personne__isnull=True, 
                    entreprise__isnull=True
                )
                
                logger.info(f"Carte trouvée: {carte.id}, statut actuel: {carte.statut}")
                
                carte.entreprise = entreprise
                carte.statut = 'ACTIVE'
                carte.date_activation = timezone.now()
                carte.save()
                
                logger.info(f"Carte {carte.id} assignée avec succès à l'entreprise {entreprise.id}")
                assigned_cards_info.append(CarteRFIDSerializer(carte).data)
                
            except CarteRFID.DoesNotExist:
                error_msg = f"Carte RFID {carte_id} non trouvée ou déjà assignée."
                logger.warning(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Erreur lors de l'assignation de la carte {carte_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            return Response({
                "message": "Certaines cartes ont été assignées, mais des erreurs sont survenues.",
                "assigned_cards": assigned_cards_info,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS if assigned_cards_info else status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Cartes assignées avec succès.",
            "assigned_cards": assigned_cards_info
        }, status=status.HTTP_200_OK)


class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]


# ViewSet pour les cartes RFID disponibles
class CarteRFIDDisponibleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CarteRFIDSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CarteRFID.objects.filter(
            personne__isnull=True, 
            entreprise__isnull=True
        ).exclude(statut__in=['PERDUE', 'VOLEE'])
