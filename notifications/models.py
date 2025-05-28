import uuid
from django.db import models
from django.db.models import JSONField
from identites.models import Utilisateur


class Notification(models.Model):
    TYPE_NOTIFICATION_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
        ('SUCCESS', 'Succès'),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push'),
        ('INTERNE', 'Interne'),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('CRITIQUE', 'Critique'),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ENVOYE', 'Envoyé'),
        ('ECHEC', 'Échec'),
        ('LU', 'Lu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    type_notification = models.CharField(max_length=20, choices=TYPE_NOTIFICATION_CHOICES)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    titre = models.CharField(max_length=255)
    message = models.TextField()
    donnees_contexte = JSONField(default=dict, blank=True)
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMALE')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    tentatives_envoi = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    date_lecture = models.DateTimeField(null=True, blank=True)
    expire_le = models.DateTimeField(null=True, blank=True)
    reference_objet = models.CharField(max_length=255, blank=True)
    type_objet = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['destinataire', 'statut']),
            models.Index(fields=['type_notification', 'date_creation']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.destinataire.username}"
