import csv
import json
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Rechargement, Transaction
from .serializers import (RechargementSerializer, TransactionDetailSerializer,
                          TransactionSerializer)
from .tasks import process_rechargement, process_transaction


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les transactions selon l'utilisateur connecté"""
        user = self.request.user
        # Si c'est un client, on filtre par ses cartes
        if hasattr(user, 'cartes'):
            return Transaction.objects.filter(carte__utilisateur=user)
        # Si c'est un admin, on retourne toutes les transactions
        return Transaction.objects.all()
    
    def create(self, request, *args, **kwargs):
        """Crée une transaction et la traite de manière asynchrone"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Création de la transaction
        transaction_obj = serializer.save()
        
        # Traitement asynchrone
        process_transaction.delay(str(transaction_obj.id))
        
        return Response(
            {
                'message': 'Transaction créée et en cours de traitement',
                'transaction_id': str(transaction_obj.id),
                'status': 'EN_COURS'
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Relance le traitement d'une transaction"""
        transaction_obj = self.get_object()
        
        if transaction_obj.statut in ['ECHOUEE', 'EN_COURS']:
            process_transaction.delay(str(transaction_obj.id))
            return Response({'message': 'Retraitement lancé'})
        else:
            return Response(
                {'error': 'Transaction déjà validée'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def detailed_history(self, request):
        """Récupère l'historique détaillé avec filtres et statistiques"""
        # Paramètres de filtrage
        transaction_type = request.query_params.get('type')
        statut = request.query_params.get('status')
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        
        # Construction de la requête
        queryset = self.get_queryset()
        
        # Filtres
        if transaction_type:
            queryset = queryset.filter(type_transaction=transaction_type.upper())
        
        if statut:
            queryset = queryset.filter(statut=statut.upper())
        
        if date_from:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            queryset = queryset.filter(date_transaction__gte=date_from_obj)
        
        if date_to:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            queryset = queryset.filter(date_transaction__lte=date_to_obj)
        
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(reference_interne__icontains=search) |
                Q(merchant_nom__icontains=search)
            )
        
        # Ordonner par date décroissante
        queryset = queryset.order_by('-date_transaction')
        
        # Statistiques globales
        stats = {
            'totalTransactions': queryset.count(),
            'totalDepenses': queryset.filter(
                type_transaction__in=['ACHAT', 'RETRAIT', 'TRANSFERT']
            ).aggregate(total=Sum('montant'))['total'] or 0,
            'totalRecus': queryset.filter(
                type_transaction='RECHARGE'
            ).aggregate(total=Sum('montant'))['total'] or 0,
            'transactionsMoyennes': queryset.aggregate(avg=Avg('montant'))['avg'] or 0
        }
        
        # Pagination
        total = queryset.count()
        offset = (page - 1) * limit
        transactions = queryset[offset:offset + limit]
        
        # Sérialisation
        serializer = TransactionDetailSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data,
            'total': total,
            'page': page,
            'totalPages': (total + limit - 1) // limit,
            'stats': stats
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Récupère les statistiques détaillées"""
        period = request.query_params.get('period', '30d')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        # Calcul de la période
        now = timezone.now()
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        elif period == '1y':
            start_date = now - timedelta(days=365)
        elif period == 'custom' and date_from and date_to:
            start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            now = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        else:
            start_date = now - timedelta(days=30)
        
        # Filtrer les transactions
        queryset = self.get_queryset().filter(
            date_transaction__gte=start_date,
            date_transaction__lte=now
        )
        
        # Statistiques générales
        total_transactions = queryset.count()
        total_depenses = queryset.filter(
            type_transaction__in=['ACHAT', 'RETRAIT', 'TRANSFERT']
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        total_recus = queryset.filter(
            type_transaction='RECHARGE'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        transactions_moyennes = queryset.aggregate(avg=Avg('montant'))['avg'] or 0
        
        # Répartition par type
        repartition_par_type = list(queryset.values('type_transaction').annotate(
            count=Count('id'),
            amount=Sum('montant')
        ))
        
        # Évolution mensuelle
        evolution_mensuelle = list(
            queryset.annotate(month=TruncMonth('date_transaction'))
            .values('month')
            .annotate(
                depenses=Sum('montant', filter=Q(type_transaction__in=['ACHAT', 'RETRAIT', 'TRANSFERT'])),
                recus=Sum('montant', filter=Q(type_transaction='RECHARGE'))
            )
            .order_by('month')
        )
        
        # Top commerçants
        top_commercants = list(
            queryset.filter(type_transaction='ACHAT')
            .values('merchant_nom')
            .annotate(
                amount=Sum('montant'),
                count=Count('id')
            )
            .order_by('-amount')[:5]
        )
        
        return Response({
            'totalTransactions': total_transactions,
            'totalDepenses': float(total_depenses),
            'totalRecus': float(total_recus),
            'transactionsMoyennes': float(transactions_moyennes),
            'repartitionParType': [
                {
                    'type': item['type_transaction'],
                    'count': item['count'],
                    'amount': float(item['amount'] or 0)
                }
                for item in repartition_par_type
            ],
            'evolutionMensuelle': [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'depenses': float(item['depenses'] or 0),
                    'recus': float(item['recus'] or 0)
                }
                for item in evolution_mensuelle
            ],
            'topCommerçants': [
                {
                    'name': item['merchant_nom'] or 'Commerçant inconnu',
                    'amount': float(item['amount']),
                    'count': item['count']
                }
                for item in top_commercants
            ]
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Exporte les transactions"""
        format_type = request.query_params.get('format', 'csv')
        transaction_type = request.query_params.get('type')
        statut = request.query_params.get('status')
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        
        # Construction de la requête
        queryset = self.get_queryset()
        
        # Filtres
        if transaction_type:
            queryset = queryset.filter(type_transaction=transaction_type.upper())
        if statut:
            queryset = queryset.filter(statut=statut.upper())
        if date_from:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            queryset = queryset.filter(date_transaction__gte=date_from_obj)
        if date_to:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            queryset = queryset.filter(date_transaction__lte=date_to_obj)
        
        queryset = queryset.order_by('-date_transaction')
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Date', 'Référence', 'Type', 'Montant', 'Statut', 
                'Commerçant', 'Description', 'Solde Avant', 'Solde Après'
            ])
            
            for transaction in queryset:
                writer.writerow([
                    transaction.date_transaction.strftime('%Y-%m-%d %H:%M:%S'),
                    transaction.reference_interne,
                    transaction.get_type_transaction_display(),
                    transaction.montant,
                    transaction.get_statut_display(),
                    transaction.merchant_nom or '-',
                    transaction.description or '-',
                    transaction.solde_avant,
                    transaction.solde_apres
                ])
            
            return response
        
        # Pour les autres formats (PDF, Excel), on retournerait les données
        # et les traiterait côté frontend
        return Response({'error': 'Format non supporté'}, status=400)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Génère le reçu d'une transaction"""
        transaction_obj = self.get_object()
        
        # Générer le reçu (ici on retourne un JSON, mais on pourrait générer un PDF)
        receipt_data = {
            'transaction_id': str(transaction_obj.id),
            'reference': transaction_obj.reference_interne,
            'date': transaction_obj.date_transaction.isoformat(),
            'type': transaction_obj.get_type_transaction_display(),
            'montant': float(transaction_obj.montant),
            'statut': transaction_obj.get_statut_display(),
            'merchant': transaction_obj.merchant_nom,
            'description': transaction_obj.description,
            'carte': str(transaction_obj.carte.numero_carte),
            'solde_avant': float(transaction_obj.solde_avant),
            'solde_apres': float(transaction_obj.solde_apres)
        }
        
        # En production, on générerait un PDF ici
        response = HttpResponse(
            json.dumps(receipt_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="recu_{transaction_obj.reference_interne}.json"'
        
        return response

    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        """Demande de remboursement"""
        transaction_obj = self.get_object()
        reason = request.data.get('reason', '')
        
        if transaction_obj.statut != 'VALIDEE':
            return Response(
                {'error': 'Seules les transactions validées peuvent être remboursées'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ici on pourrait créer une demande de remboursement
        # Pour l'instant, on simule juste la réponse
        return Response({
            'message': 'Demande de remboursement enregistrée',
            'transaction_id': str(transaction_obj.id),
            'reason': reason
        })


class RechargementViewSet(viewsets.ModelViewSet):
    queryset = Rechargement.objects.all()
    serializer_class = RechargementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les rechargements selon l'utilisateur connecté"""
        user = self.request.user
        if hasattr(user, 'cartes'):
            return Rechargement.objects.filter(carte__utilisateur=user)
        return Rechargement.objects.all()
    
    def create(self, request, *args, **kwargs):
        """Crée un rechargement et le traite de manière asynchrone"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Création du rechargement
        rechargement_obj = serializer.save()
        
        # Traitement asynchrone
        process_rechargement.delay(str(rechargement_obj.id))
        
        return Response(
            {
                'message': 'Rechargement créé et en cours de traitement',
                'rechargement_id': str(rechargement_obj.id),
                'status': 'EN_ATTENTE'
            },
            status=status.HTTP_201_CREATED
        )
