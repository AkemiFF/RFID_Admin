from django.core.management.base import BaseCommand
from authentication.models import Permission, Role


class Command(BaseCommand):
    help = 'Crée les permissions et rôles par défaut'

    def handle(self, *args, **options):
        self.stdout.write('Création des permissions par défaut...')
        
        # Définir les permissions par défaut
        default_permissions = [
            # Cartes
            ('CARTES.CREATE', 'Créer des cartes', 'CARTES', 'CREATE'),
            ('CARTES.READ', 'Lire les cartes', 'CARTES', 'READ'),
            ('CARTES.UPDATE', 'Modifier les cartes', 'CARTES', 'UPDATE'),
            ('CARTES.DELETE', 'Supprimer les cartes', 'CARTES', 'DELETE'),
            ('CARTES.BLOCK', 'Bloquer les cartes', 'CARTES', 'BLOCK'),
            ('CARTES.UNBLOCK', 'Débloquer les cartes', 'CARTES', 'UNBLOCK'),
            
            # Transactions
            ('TRANSACTIONS.CREATE', 'Créer des transactions', 'TRANSACTIONS', 'CREATE'),
            ('TRANSACTIONS.READ', 'Lire les transactions', 'TRANSACTIONS', 'READ'),
            ('TRANSACTIONS.UPDATE', 'Modifier les transactions', 'TRANSACTIONS', 'UPDATE'),
            ('TRANSACTIONS.DELETE', 'Supprimer les transactions', 'TRANSACTIONS', 'DELETE'),
            ('TRANSACTIONS.APPROVE', 'Approuver les transactions', 'TRANSACTIONS', 'APPROVE'),
            ('TRANSACTIONS.REJECT', 'Rejeter les transactions', 'TRANSACTIONS', 'REJECT'),
            
            # Identités
            ('IDENTITES.CREATE', 'Créer des identités', 'IDENTITES', 'CREATE'),
            ('IDENTITES.READ', 'Lire les identités', 'IDENTITES', 'READ'),
            ('IDENTITES.UPDATE', 'Modifier les identités', 'IDENTITES', 'UPDATE'),
            ('IDENTITES.DELETE', 'Supprimer les identités', 'IDENTITES', 'DELETE'),
            
            # Documents
            ('DOCUMENTS.CREATE', 'Créer des documents', 'DOCUMENTS', 'CREATE'),
            ('DOCUMENTS.READ', 'Lire les documents', 'DOCUMENTS', 'READ'),
            ('DOCUMENTS.UPDATE', 'Modifier les documents', 'DOCUMENTS', 'UPDATE'),
            ('DOCUMENTS.DELETE', 'Supprimer les documents', 'DOCUMENTS', 'DELETE'),
            
            # Logs
            ('LOGS.READ', 'Lire les logs', 'LOGS', 'READ'),
            ('LOGS.EXPORT', 'Exporter les logs', 'LOGS', 'EXPORT'),
            
            # Notifications
            ('NOTIFICATIONS.CREATE', 'Créer des notifications', 'NOTIFICATIONS', 'CREATE'),
            ('NOTIFICATIONS.READ', 'Lire les notifications', 'NOTIFICATIONS', 'READ'),
            ('NOTIFICATIONS.UPDATE', 'Modifier les notifications', 'NOTIFICATIONS', 'UPDATE'),
            ('NOTIFICATIONS.DELETE', 'Supprimer les notifications', 'NOTIFICATIONS', 'DELETE'),
            
            # Paramètres
            ('PARAMETRES.READ', 'Lire les paramètres', 'PARAMETRES', 'READ'),
            ('PARAMETRES.UPDATE', 'Modifier les paramètres', 'PARAMETRES', 'UPDATE'),
            
            # API Management
            ('API_MANAGEMENT.CREATE', 'Créer des clients API', 'API_MANAGEMENT', 'CREATE'),
            ('API_MANAGEMENT.READ', 'Lire les clients API', 'API_MANAGEMENT', 'READ'),
            ('API_MANAGEMENT.UPDATE', 'Modifier les clients API', 'API_MANAGEMENT', 'UPDATE'),
            ('API_MANAGEMENT.DELETE', 'Supprimer les clients API', 'API_MANAGEMENT', 'DELETE'),
            
            # Rapports
            ('RAPPORTS.READ', 'Lire les rapports', 'RAPPORTS', 'READ'),
            ('RAPPORTS.EXPORT', 'Exporter les rapports', 'RAPPORTS', 'EXPORT'),
            
            # Système
            ('SYSTEM.READ', 'Lire les paramètres système', 'SYSTEM', 'READ'),
            ('SYSTEM.UPDATE', 'Modifier les paramètres système', 'SYSTEM', 'UPDATE'),
        ]
        
        # Créer les permissions
        for name, description, resource_type, action_type in default_permissions:
            permission, created = Permission.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'resource_type': resource_type,
                    'action_type': action_type,
                }
            )
            if created:
                self.stdout.write(f'Permission créée: {name}')
        
        # Créer les rôles par défaut
        self.stdout.write('Création des rôles par défaut...')
        
        # Rôle Admin - Toutes les permissions
        admin_role, created = Role.objects.get_or_create(
            name='Administrateur',
            defaults={
                'description': 'Accès complet au système',
                'is_system_role': True,
            }
        )
        if created:
            admin_role.permissions.set(Permission.objects.all())
            self.stdout.write('Rôle Administrateur créé')
        
        # Rôle Superviseur - Permissions de lecture et gestion
        superviseur_permissions = Permission.objects.filter(
            action_type__in=['READ', 'CREATE', 'UPDATE', 'APPROVE', 'REJECT']
        )
        superviseur_role, created = Role.objects.get_or_create(
            name='Superviseur',
            defaults={
                'description': 'Supervision et gestion des opérations',
                'is_system_role': True,
            }
        )
        if created:
            superviseur_role.permissions.set(superviseur_permissions)
            self.stdout.write('Rôle Superviseur créé')
        
        # Rôle Opérateur - Permissions limitées
        operateur_permissions = Permission.objects.filter(
            action_type__in=['READ', 'CREATE', 'UPDATE'],
            resource_type__in=['CARTES', 'TRANSACTIONS', 'IDENTITES']
        )
        operateur_role, created = Role.objects.get_or_create(
            name='Opérateur',
            defaults={
                'description': 'Opérations courantes sur les cartes et transactions',
                'is_system_role': True,
            }
        )
        if created:
            operateur_role.permissions.set(operateur_permissions)
            self.stdout.write('Rôle Opérateur créé')
        
        # Rôle Agent - Permissions de base
        agent_permissions = Permission.objects.filter(
            action_type='READ',
            resource_type__in=['CARTES', 'TRANSACTIONS', 'IDENTITES']
        )
        agent_role, created = Role.objects.get_or_create(
            name='Agent',
            defaults={
                'description': 'Consultation des données de base',
                'is_system_role': True,
            }
        )
        if created:
            agent_role.permissions.set(agent_permissions)
            self.stdout.write('Rôle Agent créé')
        
        self.stdout.write(
            self.style.SUCCESS('Permissions et rôles par défaut créés avec succès!')
        )
