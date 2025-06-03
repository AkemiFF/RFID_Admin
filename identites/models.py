import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import JSONField


class Personne(models.Model):
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('SUSPENDU', 'Suspendu'),
    ]
    
    TYPE_PIECE_CHOICES = [
        ('CNI', 'Carte Nationale d\'Identité'),
        ('PASSEPORT', 'Passeport'),
        ('PERMIS', 'Permis de Conduire'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    date_naissance = models.DateField(blank= True)
    lieu_naissance = models.CharField(max_length=255, blank=True)
    nationalite = models.CharField(max_length=100)
    profession = models.CharField(max_length=255, blank=True)
    type_piece = models.CharField(max_length=20, choices=TYPE_PIECE_CHOICES)
    numero_piece = models.CharField(max_length=100, unique=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.UUIDField(null=True, blank=True)
    modifie_par = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'personnes'
        verbose_name = 'Personne'
        verbose_name_plural = 'Personnes'

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Entreprise(models.Model):
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDUE', 'Suspendue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raison_sociale = models.CharField(max_length=255)
    forme_juridique = models.CharField(max_length=100)
    stat = models.CharField(max_length=14, unique=True)
    nif = models.CharField(max_length=9, unique=True)
    tva_intracom = models.CharField(max_length=20, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    adresse_siege = models.TextField(blank = True)
    date_creation_entreprise = models.DateField(blank= True)
    secteur_activite = models.CharField(max_length=255)
    numero_rcs = models.CharField(max_length=50, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIVE')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.UUIDField(null=True, blank=True)
    modifie_par = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'entreprises'
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'

    def __str__(self):
        return self.raison_sociale


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('OPERATEUR', 'Opérateur'),
        ('AGENT', 'Agent'),
        ('SUPERVISEUR', 'Superviseur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.ForeignKey(Personne, on_delete=models.CASCADE, null=True, blank=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region_assignee = models.CharField(max_length=100, blank=True)
    permissions_speciales = JSONField(default=dict, blank=True)
    actif = models.BooleanField(default=True)
    force_changement_mdp = models.BooleanField(default=False)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    tentatives_connexion_echouees = models.IntegerField(default=0)
    compte_verrouille_jusqu = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    cree_par = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'utilisateurs'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.username
