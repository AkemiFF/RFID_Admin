from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging
import json
from .models import LogSysteme
from cartes.models import CarteRFID
from transactions.models import Transaction

logger = logging.getLogger(__name__)

@shared_task
def generate_daily_reports():
    """Génère les rapports quotidiens du système"""
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Statistiques des transactions
        daily_transactions = Transaction.objects.filter(
            date_transaction__date=yesterday
        ).aggregate(
            total_count=Count('id'),
            validated_count=Count('id', filter=Q(statut='VALIDEE')),
            failed_count=Count('id', filter=Q(statut='ECHOUEE'))
        )
        
        # Statistiques des cartes
        active_cards = CarteRFID.objects.filter(statut='ACTIVE').count()
        blocked_cards = CarteRFID.objects.filter(statut='BLOQUEE').count()
        
        # Statistiques des logs
        error_logs = LogSysteme.objects.filter(
            date_creation__date=yesterday,
            niveau__in=['ERROR', 'CRITICAL']
        ).count()
        
        # Création du rapport
        report_data = {
            'date': str(yesterday),
            'transactions': daily_transactions,
            'cartes': {
                'actives': active_cards,
                'bloquees': blocked_cards
            },
            'erreurs_systeme': error_logs,
            'generated_at': timezone.now().isoformat()
        }
        
        # Enregistrement du rapport dans les logs
        LogSysteme.objects.create(
            niveau='INFO',
            action='RAPPORT_QUOTIDIEN_GENERE',
            module='logs',
            message=f'Rapport quotidien généré pour le {yesterday}',
            donnees_apres=report_data
        )
        
        # Envoi du rapport aux administrateurs
        send_report_to_admins.delay(report_data)
        
        logger.info(f"Rapport quotidien généré pour le {yesterday}")
        return f"Rapport généré pour le {yesterday}"
        
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du rapport quotidien: {exc}")
        return f"Erreur: {exc}"

@shared_task
def send_report_to_admins(report_data):
    """Envoie le rapport aux administrateurs"""
    try:
        from identites.models import Utilisateur
        from transactions.tasks import create_notification_task
        
        # Récupération des administrateurs
        admins = Utilisateur.objects.filter(role='ADMIN', actif=True)
        
        # Formatage du rapport
        report_text = format_report_text(report_data)
        
        for admin in admins:
            create_notification_task.delay(
                str(admin.id),
                'INFO',
                f'Rapport quotidien - {report_data["date"]}',
                report_text,
                'EMAIL'
            )
        
        logger.info(f"Rapport envoyé à {admins.count()} administrateurs")
        return f"Rapport envoyé à {admins.count()} administrateurs"
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi du rapport: {exc}")
        return f"Erreur: {exc}"

def format_report_text(report_data):
    """Formate le rapport en texte lisible"""
    return f"""
Rapport quotidien du système RFID - {report_data['date']}

TRANSACTIONS:
- Total: {report_data['transactions']['total_count']}
- Validées: {report_data['transactions']['validated_count']}
- Échouées: {report_data['transactions']['failed_count']}

CARTES:
- Actives: {report_data['cartes']['actives']}
- Bloquées: {report_data['cartes']['bloquees']}

SYSTÈME:
- Erreurs système: {report_data['erreurs_systeme']}

Rapport généré le {report_data['generated_at']}
"""

@shared_task
def cleanup_old_logs():
    """Nettoie les anciens logs selon la politique de rétention"""
    try:
        # Suppression des logs de plus de 90 jours (sauf CRITICAL)
        cutoff_date = timezone.now() - timedelta(days=90)
        
        old_logs = LogSysteme.objects.filter(
            date_creation__lt=cutoff_date
        ).exclude(niveau='CRITICAL')
        
        deleted_count = old_logs.count()
        old_logs.delete()
        
        # Suppression des logs CRITICAL de plus de 1 an
        critical_cutoff = timezone.now() - timedelta(days=365)
        old_critical = LogSysteme.objects.filter(
            date_creation__lt=critical_cutoff,
            niveau='CRITICAL'
        )
        
        critical_deleted = old_critical.count()
        old_critical.delete()
        
        total_deleted = deleted_count + critical_deleted
        
        # Log de l'opération de nettoyage
        LogSysteme.objects.create(
            niveau='INFO',
            action='NETTOYAGE_LOGS',
            module='logs',
            message=f'Nettoyage automatique: {total_deleted} logs supprimés'
        )
        
        logger.info(f"Nettoyage des logs: {total_deleted} entrées supprimées")
        return f"Nettoyage terminé: {total_deleted} logs supprimés"
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des logs: {exc}")
        return f"Erreur: {exc}"

@shared_task
def monitor_system_health():
    """Surveille la santé du système"""
    try:
        # Vérification des erreurs récentes
        recent_errors = LogSysteme.objects.filter(
            niveau__in=['ERROR', 'CRITICAL'],
            date_creation__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        # Vérification des transactions échouées
        failed_transactions = Transaction.objects.filter(
            statut='ECHOUEE',
            date_transaction__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        # Vérification des cartes bloquées récemment
        recently_blocked = CarteRFID.objects.filter(
            statut='BLOQUEE',
            date_modification__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        # Alertes si nécessaire
        alerts = []
        
        if recent_errors > 10:
            alerts.append(f"Nombre élevé d'erreurs système: {recent_errors}")
        
        if failed_transactions > 20:
            alerts.append(f"Nombre élevé de transactions échouées: {failed_transactions}")
        
        if recently_blocked > 5:
            alerts.append(f"Nombre élevé de cartes bloquées: {recently_blocked}")
        
        # Envoi d'alertes si nécessaire
        if alerts:
            send_system_alerts.delay(alerts)
        
        # Log de surveillance
        LogSysteme.objects.create(
            niveau='INFO',
            action='SURVEILLANCE_SYSTEME',
            module='logs',
            message='Surveillance automatique du système',
            donnees_apres={
                'erreurs_recentes': recent_errors,
                'transactions_echouees': failed_transactions,
                'cartes_bloquees': recently_blocked,
                'alertes': alerts
            }
        )
        
        logger.info(f"Surveillance système: {len(alerts)} alertes générées")
        return f"Surveillance terminée: {len(alerts)} alertes"
        
    except Exception as exc:
        logger.error(f"Erreur lors de la surveillance système: {exc}")
        return f"Erreur: {exc}"

@shared_task
def send_system_alerts(alerts):
    """Envoie les alertes système aux administrateurs"""
    try:
        from identites.models import Utilisateur
        from transactions.tasks import create_notification_task
        
        admins = Utilisateur.objects.filter(role='ADMIN', actif=True)
        
        alert_message = "ALERTES SYSTÈME:\n\n" + "\n".join([f"- {alert}" for alert in alerts])
        
        for admin in admins:
            create_notification_task.delay(
                str(admin.id),
                'WARNING',
                'Alertes système détectées',
                alert_message,
                'EMAIL'
            )
        
        logger.warning(f"Alertes système envoyées à {admins.count()} administrateurs")
        return f"Alertes envoyées à {admins.count()} administrateurs"
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi des alertes: {exc}")
        return f"Erreur: {exc}"
