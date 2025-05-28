import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField
from identites.models import Utilisateur


class ApiClient(models.Model):
    TYPE_CLIENT_CHOICES = [
        ('PUBLIC', 'Public'),
        ('CONFIDENTIEL', 'Confidentiel'),
        ('INTERNE', 'Interne'),
    ]
    
    NIVEAU_ACCES_CHOICES = [
        ('LECTURE', 'Lecture'),
        ('ECRITURE', 'Écriture'),
        ('ADMIN', 'Administrateur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_client = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organisation = models.CharField(max_length=255, blank=True)
    contact_technique = models.CharField(max_length=255, blank=True)
    email_contact = models.EmailField(blank=True)
    client_id = models.CharField(max_length=100, unique=True)
    client_secret = models.CharField(max_length=255)
    type_client = models.CharField(max_length=20, choices=TYPE_CLIENT_CHOICES)
    niveau_acces = models.CharField(max_length=20, choices=NIVEAU_ACCES_CHOICES)
    scopes_autorises = JSONField(default=list, blank=True)
    adresses_ip_autorisees = JSONField(default=list, blank=True)
    rate_limit_par_minute = models.IntegerField(default=60)
    rate_limit_par_jour = models.IntegerField(default=10000)
    webhook_url = models.URLField(max_length=500, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    derniere_utilisation = models.DateTimeField(null=True, blank=True)
    nombre_requetes_total = models.BigIntegerField(default=0)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'api_clients'
        verbose_name = 'Client API'
        verbose_name_plural = 'Clients API'

    def __str__(self):
        return self.nom_client


class ApiLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(ApiClient, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=255)
    methode_http = models.CharField(max_length=10)
    adresse_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    parametres_requete = JSONField(default=dict, blank=True)
    corps_requete = models.TextField(blank=True)
    code_reponse = models.IntegerField()
    taille_reponse = models.IntegerField(default=0)
    duree_traitement = models.IntegerField()  # en millisecondes
    erreur_message = models.TextField(blank=True)
    carte_concernee = models.CharField(max_length=100, blank=True)
    montant_transaction = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date_requete = models.DateTimeField(auto_now_add=True)
    trace_id = models.CharField(max_length=100, blank=True)
    session_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'api_logs'
        verbose_name = 'Log API'
        verbose_name_plural = 'Logs API'
        indexes = [
            models.Index(fields=['client', 'date_requete']),
            models.Index(fields=['endpoint', 'date_requete']),
            models.Index(fields=['code_reponse', 'date_requete']),
        ]

    def __str__(self):
        return f"{self.methode_http} {self.endpoint} - {self.code_reponse}"
