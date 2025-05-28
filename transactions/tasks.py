from celery import shared_task
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging
from .models import Transaction, Rechargement
from cartes.models import CarteRFID
from notifications.models import Notification
from logs.models import LogSysteme

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_transaction(self, transaction_id):
    """Traite une transaction de manière asynchrone"""
    try:
        with transaction.atomic():
            trans = Transaction.objects.select_for_update().get(id=transaction_id)
            
            if trans.statut != 'EN_COURS':
                return f"Transaction {transaction_id} déjà traitée"
            
            carte = trans.carte
            
            # Vérifications de sécurité
            if carte.statut != 'ACTIVE':
                trans.statut = 'ECHOUEE'
                trans.code_erreur = 'CARTE_INACTIVE'
                trans.message_erreur = 'Carte non active'
                trans.save()
                return f"Transaction échouée: carte inactive"
            
            # Vérification du solde pour les débits
            if trans.type_transaction in ['ACHAT', 'RETRAIT']:
                if carte.solde < trans.montant:
                    trans.statut = 'ECHOUEE'
                    trans.code_erreur = 'SOLDE_INSUFFISANT'
                    trans.message_erreur = 'Solde insuffisant'
                    trans.save()
                    
                    # Notification de solde insuffisant
                    create_notification_task.delay(
                        str(carte.personne.id if carte.personne else carte.entreprise.id),
                        'WARNING',
                        'Solde insuffisant',
                        f'Tentative de transaction de {trans.montant}€ refusée pour solde insuffisant.',
                        'EMAIL'
                    )
                    return f"Transaction échouée: solde insuffisant"
                
                # Débit du compte
                carte.solde -= trans.montant
                trans.solde_apres = carte.solde
            
            elif trans.type_transaction == 'RECHARGE':
                # Crédit du compte
                carte.solde += trans.montant
                trans.solde_apres = carte.solde
            
            # Mise à jour de la carte
            carte.derniere_utilisation = timezone.now()
            carte.nombre_transactions += 1
            carte.save()
            
            # Validation de la transaction
            trans.statut = 'VALIDEE'
            trans.date_validation = timezone.now()
            trans.save()
            
            # Log de la transaction
            LogSysteme.objects.create(
                niveau='INFO',
                action='TRANSACTION_VALIDEE',
                module='transactions',
                carte_concernee=carte,
                transaction_concernee=trans,
                message=f'Transaction {trans.reference_interne} validée avec succès'
            )
            
            # Notification de succès
            if trans.type_transaction == 'RECHARGE':
                create_notification_task.delay(
                    str(carte.personne.id if carte.personne else carte.entreprise.id),
                    'SUCCESS',
                    'Rechargement effectué',
                    f'Votre carte a été rechargée de {trans.montant}€. Nouveau solde: {carte.solde}€',
                    'SMS'
                )
            
            logger.info(f"Transaction {transaction_id} traitée avec succès")
            return f"Transaction {transaction_id} validée"
            
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} introuvable")
        return f"Transaction {transaction_id} introuvable"
    except Exception as exc:
        logger.error(f"Erreur lors du traitement de la transaction {transaction_id}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            # Marquer la transaction comme échouée après épuisement des tentatives
            try:
                trans = Transaction.objects.get(id=transaction_id)
                trans.statut = 'ECHOUEE'
                trans.code_erreur = 'ERREUR_SYSTEME'
                trans.message_erreur = str(exc)
                trans.save()
            except:
                pass
            return f"Échec définitif du traitement après {self.max_retries} tentatives"

@shared_task
def process_pending_transactions():
    """Traite les transactions en attente"""
    try:
        pending_transactions = Transaction.objects.filter(
            statut='EN_COURS',
            date_transaction__gte=timezone.now() - timezone.timedelta(hours=1)
        )[:50]
        
        processed = 0
        for trans in pending_transactions:
            process_transaction.delay(str(trans.id))
            processed += 1
        
        logger.info(f"Lancement du traitement de {processed} transactions en attente")
        return f"Traitement de {processed} transactions lancé"
        
    except Exception as exc:
        logger.error(f"Erreur lors du traitement des transactions en attente: {exc}")
        return f"Erreur: {exc}"

@shared_task(bind=True, max_retries=3)
def process_rechargement(self, rechargement_id):
    """Traite un rechargement de manière asynchrone"""
    try:
        with transaction.atomic():
            rechargement = Rechargement.objects.select_for_update().get(id=rechargement_id)
            
            if rechargement.statut_paiement != 'EN_ATTENTE':
                return f"Rechargement {rechargement_id} déjà traité"
            
            # Simulation de la vérification du paiement
            # Ici vous intégreriez avec votre système de paiement
            payment_verified = verify_payment(rechargement)
            
            if payment_verified:
                # Création de la transaction de rechargement
                trans = Transaction.objects.create(
                    carte=rechargement.carte,
                    type_transaction='RECHARGE',
                    montant=rechargement.montant_recharge,
                    solde_avant=rechargement.carte.solde,
                    reference_interne=f"RECH_{rechargement.recu_numero}",
                    description=f"Rechargement via {rechargement.mode_paiement}",
                    statut='EN_COURS'
                )
                
                rechargement.transaction = trans
                rechargement.statut_paiement = 'CONFIRME'
                rechargement.date_confirmation = timezone.now()
                rechargement.save()
                
                # Traitement de la transaction
                process_transaction.delay(str(trans.id))
                
                logger.info(f"Rechargement {rechargement_id} confirmé")
                return f"Rechargement {rechargement_id} confirmé"
            else:
                rechargement.statut_paiement = 'ECHEC'
                rechargement.save()
                
                logger.warning(f"Rechargement {rechargement_id} échoué - paiement non vérifié")
                return f"Rechargement {rechargement_id} échoué"
                
    except Exception as exc:
        logger.error(f"Erreur lors du traitement du rechargement {rechargement_id}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            return f"Échec définitif du traitement après {self.max_retries} tentatives"

def verify_payment(rechargement):
    """Vérifie le paiement selon le mode de paiement"""
    # Simulation - à remplacer par l'intégration réelle
    if rechargement.mode_paiement == 'MOBILE_MONEY':
        # Vérification avec l'API Mobile Money
        return True
    elif rechargement.mode_paiement == 'CARTE_BANCAIRE':
        # Vérification avec l'API bancaire
        return True
    elif rechargement.mode_paiement == 'VIREMENT':
        # Vérification du virement
        return True
    else:
        return True

@shared_task
def create_notification_task(user_id, type_notif, titre, message, canal='EMAIL'):
    """Crée une notification de manière asynchrone"""
    try:
        from identites.models import Utilisateur
        
        user = Utilisateur.objects.get(id=user_id)
        
        notification = Notification.objects.create(
            destinataire=user,
            type_notification=type_notif,
            canal=canal,
            titre=titre,
            message=message,
            priorite='NORMALE'
        )
        
        # Envoi immédiat selon le canal
        if canal == 'EMAIL':
            from notifications.tasks import send_email_notification
            send_email_notification.delay(str(notification.id))
        elif canal == 'SMS':
            from notifications.tasks import send_sms_notification
            send_sms_notification.delay(str(notification.id))
        elif canal == 'PUSH':
            from notifications.tasks import send_push_notification
            send_push_notification.delay(str(notification.id))
        
        return f"Notification créée et envoyée: {notification.id}"
        
    except Exception as exc:
        logger.error(f"Erreur lors de la création de notification: {exc}")
        return f"Erreur: {exc}"
