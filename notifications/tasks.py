from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import requests
from .models import Notification

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    """Envoie une notification par email"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.canal != 'EMAIL':
            return f"Notification {notification_id} n'est pas de type EMAIL"
        
        # Récupération de l'email du destinataire
        email = notification.destinataire.email
        if not email:
            notification.statut = 'ECHEC'
            notification.save()
            return f"Pas d'email pour l'utilisateur {notification.destinataire.username}"
        
        # Envoi de l'email
        send_mail(
            subject=notification.titre,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        # Mise à jour du statut
        notification.statut = 'ENVOYE'
        notification.date_envoi = timezone.now()
        notification.save()
        
        logger.info(f"Email envoyé avec succès pour la notification {notification_id}")
        return f"Email envoyé avec succès à {email}"
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} introuvable")
        return f"Notification {notification_id} introuvable"
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de l'email pour {notification_id}: {exc}")
        notification.tentatives_envoi += 1
        notification.save()
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            notification.statut = 'ECHEC'
            notification.save()
            return f"Échec définitif de l'envoi après {self.max_retries} tentatives"

@shared_task(bind=True, max_retries=3)
def send_sms_notification(self, notification_id):
    """Envoie une notification par SMS via Twilio"""
    try:
        from twilio.rest import Client
        
        notification = Notification.objects.get(id=notification_id)
        
        if notification.canal != 'SMS':
            return f"Notification {notification_id} n'est pas de type SMS"
        
        # Récupération du numéro de téléphone
        if hasattr(notification.destinataire, 'personne') and notification.destinataire.personne:
            phone = notification.destinataire.personne.telephone
        else:
            phone = getattr(notification.destinataire, 'telephone', None)
            
        if not phone:
            notification.statut = 'ECHEC'
            notification.save()
            return f"Pas de téléphone pour l'utilisateur {notification.destinataire.username}"
        
        # Configuration Twilio
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Envoi du SMS
        message = client.messages.create(
            body=f"{notification.titre}\n{notification.message}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        # Mise à jour du statut
        notification.statut = 'ENVOYE'
        notification.date_envoi = timezone.now()
        notification.donnees_contexte['twilio_sid'] = message.sid
        notification.save()
        
        logger.info(f"SMS envoyé avec succès pour la notification {notification_id}")
        return f"SMS envoyé avec succès à {phone}"
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi du SMS pour {notification_id}: {exc}")
        notification.tentatives_envoi += 1
        notification.save()
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            notification.statut = 'ECHEC'
            notification.save()
            return f"Échec définitif de l'envoi après {self.max_retries} tentatives"

@shared_task
def send_push_notification(notification_id):
    """Envoie une notification push"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.canal != 'PUSH':
            return f"Notification {notification_id} n'est pas de type PUSH"
        
        # Ici vous pouvez intégrer Firebase Cloud Messaging ou autre service push
        # Pour l'exemple, on simule l'envoi
        
        notification.statut = 'ENVOYE'
        notification.date_envoi = timezone.now()
        notification.save()
        
        logger.info(f"Push notification envoyée pour {notification_id}")
        return f"Push notification envoyée avec succès"
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de la push notification {notification_id}: {exc}")
        return f"Erreur: {exc}"

@shared_task
def cleanup_expired_notifications():
    """Nettoie les notifications expirées"""
    try:
        expired_notifications = Notification.objects.filter(
            expire_le__lt=timezone.now(),
            statut__in=['EN_ATTENTE', 'ECHEC']
        )
        
        count = expired_notifications.count()
        expired_notifications.delete()
        
        logger.info(f"Suppression de {count} notifications expirées")
        return f"Suppression de {count} notifications expirées"
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des notifications: {exc}")
        return f"Erreur: {exc}"

@shared_task
def process_notification_queue():
    """Traite la file d'attente des notifications"""
    try:
        pending_notifications = Notification.objects.filter(
            statut='EN_ATTENTE',
            tentatives_envoi__lt=3
        ).order_by('priorite', 'date_creation')[:100]
        
        processed = 0
        for notification in pending_notifications:
            if notification.canal == 'EMAIL':
                send_email_notification.delay(str(notification.id))
            elif notification.canal == 'SMS':
                send_sms_notification.delay(str(notification.id))
            elif notification.canal == 'PUSH':
                send_push_notification.delay(str(notification.id))
            
            processed += 1
        
        logger.info(f"Traitement de {processed} notifications en attente")
        return f"Traitement de {processed} notifications"
        
    except Exception as exc:
        logger.error(f"Erreur lors du traitement des notifications: {exc}")
        return f"Erreur: {exc}"
