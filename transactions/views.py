from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Transaction, Rechargement
from .serializers import TransactionSerializer, RechargementSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .tasks import process_transaction, process_rechargement


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
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

class RechargementViewSet(viewsets.ModelViewSet):
    queryset = Rechargement.objects.all()
    serializer_class = RechargementSerializer
    permission_classes = [IsAuthenticated]
    
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
