from datetime import timedelta

from authentication.permissions import IsCardOwner
from django.db.models import Avg, Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from identites.models import Entreprise, Personne
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from .models import CarteRFID, HistoriqueStatutsCarte
from .serializers import (CarteLimitsSerializer, CartePINSerializer,
                          CarteRequestSerializer, CarteRFIDDetailSerializer,
                          CarteRFIDSerializer, CarteSettingsSerializer,
                          CarteStatisticsSerializer, ClientCarteRFIDSerializer,
                          HistoriqueStatutsCarteSerializer)


class CarteRFIDViewSet(viewsets.ModelViewSet):
    queryset = CarteRFID.objects.all()
    serializer_class = CarteRFIDSerializer
    permission_classes = [IsAuthenticated]


class HistoriqueStatutsCarteViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueStatutsCarte.objects.all()
    serializer_class = HistoriqueStatutsCarteSerializer
    permission_classes = [IsAuthenticated]


class ClientCarteRFIDViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les opérations client sur les cartes RFID
    """
    serializer_class = ClientCarteRFIDSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourne uniquement les cartes appartenant au client connecté"""
        user = self.request.user
        
        # Récupérer les cartes liées à la personne ou à l'entreprise de l'utilisateur
        try:
            personne = Personne.objects.get(utilisateur=user)
            return CarteRFID.objects.filter(personne=personne)
        except Personne.DoesNotExist:
            try:
                entreprise = Entreprise.objects.get(utilisateur=user)
                return CarteRFID.objects.filter(entreprise=entreprise)
            except Entreprise.DoesNotExist:
                return CarteRFID.objects.none()

    def retrieve(self, request, *args, **kwargs):
        """Récupérer les détails d'une carte spécifique"""
        instance = self.get_object()
        serializer = CarteRFIDDetailSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def block(self, request, pk=None):
        """Bloquer une carte"""
        carte = self.get_object()
        reason = request.data.get('reason', 'Bloquée par le client')
        
        if carte.statut == 'BLOQUEE':
            return Response(
                {"detail": "La carte est déjà bloquée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder l'ancien statut
        ancien_statut = carte.statut
        
        # Mettre à jour le statut et le motif
        carte.statut = 'BLOQUEE'
        carte.motif_blocage = reason
        carte.save()
        
        # Créer un historique
        HistoriqueStatutsCarte.objects.create(
            carte=carte,
            ancien_statut=ancien_statut,
            nouveau_statut='BLOQUEE',
            motif_changement=reason,
            agent_modificateur=request.user,
            adresse_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({"detail": "Carte bloquée avec succès."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unblock(self, request, pk=None):
        """Débloquer une carte"""
        carte = self.get_object()
        
        if carte.statut != 'BLOQUEE':
            return Response(
                {"detail": "La carte n'est pas bloquée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder l'ancien statut
        ancien_statut = carte.statut
        
        # Mettre à jour le statut
        carte.statut = 'ACTIVE'
        carte.motif_blocage = ''
        carte.save()
        
        # Créer un historique
        HistoriqueStatutsCarte.objects.create(
            carte=carte,
            ancien_statut=ancien_statut,
            nouveau_statut='ACTIVE',
            motif_changement="Débloquée par le client",
            agent_modificateur=request.user,
            adresse_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({"detail": "Carte débloquée avec succès."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        """Activer une carte"""
        carte = self.get_object()
        serializer = CartePINSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if carte.date_activation:
            return Response(
                {"detail": "La carte est déjà activée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Activer la carte
        carte.date_activation = timezone.now()
        carte.statut = 'ACTIVE'
        carte.save()
        
        # Créer un historique
        HistoriqueStatutsCarte.objects.create(
            carte=carte,
            ancien_statut='',
            nouveau_statut='ACTIVE',
            motif_changement="Activation de la carte",
            agent_modificateur=request.user,
            adresse_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({"detail": "Carte activée avec succès."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_pin(self, request, pk=None):
        """Changer le PIN d'une carte"""
        carte = self.get_object()
        serializer = CartePINSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Dans un système réel, nous vérifierions l'ancien PIN et mettrions à jour le nouveau
        # Pour cet exemple, nous simulons simplement une réponse réussie
        
        return Response({"detail": "PIN modifié avec succès."})

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def limits(self, request, pk=None):
        """Mettre à jour les limites d'une carte"""
        carte = self.get_object()
        serializer = CarteLimitsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour les limites
        carte.plafond_quotidien = serializer.validated_data['plafondJournalier']
        carte.plafond_mensuel = serializer.validated_data['plafondMensuel']
        carte.save()
        
        return Response({"detail": "Limites mises à jour avec succès."})

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_settings(self, request, pk=None):
        """Mettre à jour les paramètres d'une carte"""
        carte = self.get_object()
        serializer = CarteSettingsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
        # Dans un système réel, nous mettrions à jour les paramètres dans la base de données
        # Pour cet exemple, nous simulons simplement une réponse réussie
        
        return Response({"detail": "Paramètres mis à jour avec succès."})

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def transactions(self, request, pk=None):
        """Récupérer les transactions d'une carte"""
        carte = self.get_object()
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        # Récupérer les transactions
        transactions = Transaction.objects.filter(carte=carte).order_by('-date_transaction')[offset:offset+limit]
        total = Transaction.objects.filter(carte=carte).count()
        
        # Sérialiser les transactions
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data,
            'total': total,
            'page': page,
            'totalPages': (total + limit - 1) // limit
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def request(self, request):
        """Demander une nouvelle carte"""
        serializer = CarteRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Dans un système réel, nous créerions une demande de carte
        # Pour cet exemple, nous simulons simplement une réponse réussie
        
        return Response({
            "requestId": "REQ-" + str(timezone.now().timestamp()).replace(".", ""),
            "estimatedDelivery": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def report_lost(self, request, pk=None):
        """Signaler une carte perdue"""
        carte = self.get_object()
        circumstances = request.data.get('circumstances', '')
        
        if carte.statut in ['PERDUE', 'VOLEE']:
            return Response(
                {"detail": "Cette carte a déjà été signalée comme perdue ou volée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder l'ancien statut
        ancien_statut = carte.statut
        
        # Mettre à jour le statut
        carte.statut = 'PERDUE'
        carte.motif_blocage = f"Carte signalée perdue: {circumstances}"
        carte.save()
        
        # Créer un historique
        HistoriqueStatutsCarte.objects.create(
            carte=carte,
            ancien_statut=ancien_statut,
            nouveau_statut='PERDUE',
            motif_changement=f"Carte signalée perdue: {circumstances}",
            agent_modificateur=request.user,
            adresse_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({"detail": "Carte signalée comme perdue avec succès."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def replace(self, request, pk=None):
        """Demander un remplacement de carte"""
        carte = self.get_object()
        reason = request.data.get('reason', '')
        
        # Dans un système réel, nous créerions une demande de remplacement
        # Pour cet exemple, nous simulons simplement une réponse réussie
        
        return Response({
            "requestId": "REPL-" + str(timezone.now().timestamp()).replace(".", ""),
            "cost": 15000  # Coût en ariary
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request, pk=None):
        """Récupérer les statistiques d'une carte"""
        carte = self.get_object()
        period = request.query_params.get('period', 'month')
        
        # Déterminer la date de début en fonction de la période
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # Par défaut: mois
        
        # Récupérer les transactions de la période
        transactions = Transaction.objects.filter(
            carte=carte,
            date_transaction__gte=start_date
        )
        
        # Calculer les statistiques
        total_transactions = transactions.count()
        total_amount = transactions.aggregate(Sum('montant'))['montant__sum'] or 0
        average_transaction = transactions.aggregate(Avg('montant'))['montant__avg'] or 0
        
        # Top commerçants
        top_merchants = transactions.values('commercant__nom') \
            .annotate(amount=Sum('montant'), count=Count('id')) \
            .order_by('-amount')[:5]
        
        # Utilisation quotidienne
        daily_usage = []
        current_date = start_date
        while current_date <= now:
            day_start = current_date.replace(hour=0, minute=0, second=0)
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            day_transactions = transactions.filter(
                date_transaction__gte=day_start,
                date_transaction__lte=day_end
            )
            
            daily_usage.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'amount': day_transactions.aggregate(Sum('montant'))['montant__sum'] or 0,
                'count': day_transactions.count()
            })
            
            current_date += timedelta(days=1)
        
        # Préparer la réponse
        response_data = {
            'totalTransactions': total_transactions,
            'totalAmount': total_amount,
            'averageTransaction': average_transaction,
            'topMerchants': [
                {
                    'name': merchant['commercant__nom'] or 'Inconnu',
                    'amount': merchant['amount'],
                    'count': merchant['count']
                }
                for merchant in top_merchants
            ],
            'dailyUsage': daily_usage
        }
        
        return Response(response_data)

    def get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
