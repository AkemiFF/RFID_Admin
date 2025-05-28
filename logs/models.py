import uuid
from django.db import models
from django.db.models import JSONField
from identites.models import Utilisateur
from cartes.models import CarteRFID
from transactions.models import Transaction


class LogSysteme(models.Model):
    NIVEAU_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=100)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    identite_concernee = models.UUIDField(null=True, blank=True)
    carte_concernee = models.ForeignKey(CarteRFID, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_concernee = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    donnees_avant = JSONField(default=dict, blank=True)
    donnees_apres = JSONField(default=dict, blank=True)
    duree_execution = models.IntegerField(null=True, blank=True)  # en millisecondes
    code_retour = models.CharField(max_length=20, blank=True)
    erreur_details = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    serveur_origine = models.CharField(max_length=100, blank=True)
    trace_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'logs_systeme'
        verbose_name = 'Log Système'
        verbose_name_plural = 'Logs Système'
        indexes = [
            models.Index(fields=['niveau', 'date_creation']),
            models.Index(fields=['utilisateur', 'date_creation']),
            models.Index(fields=['action', 'date_creation']),
        ]

    def __str__(self):
        return f"{self.niveau} - {self.action} - {self.date_creation}"
