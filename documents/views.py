from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import DocumentIdentite
from .serializers import DocumentIdentiteSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .tasks import process_document_ocr, generate_document_hash


class DocumentIdentiteViewSet(viewsets.ModelViewSet):
    queryset = DocumentIdentite.objects.all()
    serializer_class = DocumentIdentiteSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Upload un document et lance l'OCR asynchrone"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Création du document
        document_obj = serializer.save()
        
        # Génération du hash asynchrone
        generate_document_hash.delay(str(document_obj.id))
        
        # Traitement OCR asynchrone
        process_document_ocr.delay(str(document_obj.id))
        
        return Response(
            {
                'message': 'Document uploadé et en cours de traitement',
                'document_id': str(document_obj.id),
                'status': 'EN_ATTENTE'
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def reprocess_ocr(self, request, pk=None):
        """Relance le traitement OCR d'un document"""
        document_obj = self.get_object()
        
        if document_obj.statut_verification in ['REJETE', 'EN_ATTENTE']:
            document_obj.statut_verification = 'EN_ATTENTE'
            document_obj.save()
            
            process_document_ocr.delay(str(document_obj.id))
            return Response({'message': 'Retraitement OCR lancé'})
        else:
            return Response(
                {'error': 'Document déjà vérifié'},
                status=status.HTTP_400_BAD_REQUEST
            )
