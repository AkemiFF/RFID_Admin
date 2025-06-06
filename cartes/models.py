import uuid

from django.db import models
from django.db.models import JSONField
# Ajouter ces imports en haut du fichier
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from identites.models import Entreprise, Personne, Utilisateur


class CarteRFID(models.Model):
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BLOQUEE', 'Bloquée'),
        ('EXPIREE', 'Expirée'),
        ('PERDUE', 'Perdue'),
        ('VOLEE', 'Volée'),
        ('INACTIVE', 'Inactive'),

    ]
    
    TYPE_CARTE_CHOICES = [
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
        ('ENTREPRISE', 'Entreprise'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_uid = models.CharField(max_length=100, unique=True)
    personne = models.ForeignKey(Personne, on_delete=models.CASCADE, null=True, blank=True, related_name='cartes_rfid')
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, null=True, blank=True,related_name='cartes_rfid')
    numero_serie = models.CharField(max_length=50, unique=True)
    type_carte = models.CharField(max_length=20, choices=TYPE_CARTE_CHOICES)
    solde = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    plafond_quotidien = models.DecimalField(max_digits=15, decimal_places=2)
    plafond_mensuel = models.DecimalField(max_digits=15, decimal_places=2)
    solde_maximum = models.DecimalField(max_digits=15, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='INACTIVE')
    motif_blocage = models.TextField(blank=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    date_activation = models.DateTimeField(null=True, blank=True)
    date_expiration = models.DateField()
    lieu_emission = models.CharField(max_length=255)
    agent_emission = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    derniere_utilisation = models.DateTimeField(null=True, blank=True)
    nombre_transactions = models.IntegerField(default=0)
    version_securite = models.CharField(max_length=20)
    cle_chiffrement = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cartes_rfid'
        verbose_name = 'Carte RFID'
        verbose_name_plural = 'Cartes RFID'

    def __str__(self):
        return f"Carte {self.numero_serie}"


class HistoriqueStatutsCarte(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carte = models.ForeignKey(CarteRFID, on_delete=models.CASCADE)
    ancien_statut = models.CharField(max_length=20)
    nouveau_statut = models.CharField(max_length=20)
    motif_changement = models.TextField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    agent_modificateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    date_changement = models.DateTimeField(auto_now_add=True)
    donnees_supplementaires = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'historique_statuts_cartes'
        verbose_name = 'Historique Statut Carte'
        verbose_name_plural = 'Historiques Statuts Cartes'

    def __str__(self):
        return f"Changement {self.ancien_statut} -> {self.nouveau_statut}"


@receiver(pre_save, sender=CarteRFID)
def carte_status_change_handler(sender, instance, **kwargs):
    """Gère les changements de statut des cartes"""
    if instance.pk: 
        try:
            old_instance = CarteRFID.objects.get(pk=instance.pk)
            if old_instance.statut != instance.statut:
                HistoriqueStatutsCarte.objects.create(
                    carte=instance,
                    ancien_statut=old_instance.statut,
                    nouveau_statut=instance.statut,
                    motif_changement=instance.motif_blocage or "Changement automatique",
                    date_changement=timezone.now()
                )
                
                # Notification asynchrone du changement
                if instance.statut == 'BLOQUEE':
                    from transactions.tasks import create_notification_task
                    user_id = None
                    if instance.personne:
                        user = instance.personne.utilisateur_set.first()
                        if user:
                            user_id = str(user.id)
                    elif instance.entreprise:
                        user = instance.entreprise.utilisateur_set.first()
                        if user:
                            user_id = str(user.id)
                    
                    if user_id:
                        create_notification_task.delay(
                            user_id,
                            'WARNING',
                            'Carte bloquée',
                            f'Votre carte {instance.numero_serie} a été bloquée. Motif: {instance.motif_blocage}',
                            'SMS'
                        )
        except CarteRFID.DoesNotExist:
            pass
