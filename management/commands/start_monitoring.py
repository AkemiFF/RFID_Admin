from django.core.management.base import BaseCommand
from logs.tasks import monitor_system_health, cleanup_old_logs
from notifications.tasks import process_notification_queue
from transactions.tasks import process_pending_transactions

class Command(BaseCommand):
    help = 'Lance les tâches de monitoring et maintenance'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Lancement du monitoring système...')
        
        # Surveillance de la santé du système
        monitor_system_health.delay()
        
        # Traitement des notifications en attente
        process_notification_queue.delay()
        
        # Traitement des transactions en attente
        process_pending_transactions.delay()
        
        # Nettoyage des anciens logs
        cleanup_old_logs.delay()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Tâches de monitoring lancées avec succès!')
        )
