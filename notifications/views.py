from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .tasks import send_email_notification, send_sms_notification, send_push_notification
from django.utils import timezone


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Crée une notification et l'envoie de manière asynchrone"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Création de la notification
        notification_obj = serializer.save()
        
        # Envoi asynchrone selon le canal
        if notification_obj.canal == 'EMAIL':
            send_email_notification.delay(str(notification_obj.id))
        elif notification_obj.canal == 'SMS':
            send_sms_notification.delay(str(notification_obj.id))
        elif notification_obj.canal == 'PUSH':
            send_push_notification.delay(str(notification_obj.id))
        
        return Response(
            {
                'message': 'Notification créée et en cours d\'envoi',
                'notification_id': str(notification_obj.id),
                'canal': notification_obj.canal
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Renvoie une notification"""
        notification_obj = self.get_object()
        
        if notification_obj.statut in ['ECHEC', 'EN_ATTENTE']:
            notification_obj.statut = 'EN_ATTENTE'
            notification_obj.tentatives_envoi = 0
            notification_obj.save()
            
            if notification_obj.canal == 'EMAIL':
                send_email_notification.delay(str(notification_obj.id))
            elif notification_obj.canal == 'SMS':
                send_sms_notification.delay(str(notification_obj.id))
            elif notification_obj.canal == 'PUSH':
                send_push_notification.delay(str(notification_obj.id))
            
            return Response({'message': 'Renvoi de la notification lancé'})
        else:
            return Response(
                {'error': 'Notification déjà envoyée'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Marque les notifications comme lues"""
        notification_ids = request.data.get('notification_ids', [])
        
        updated = Notification.objects.filter(
            id__in=notification_ids,
            destinataire=request.user
        ).update(
            statut='LU',
            date_lecture=timezone.now()
        )
        
        return Response({
            'message': f'{updated} notifications marquées comme lues'
        })
