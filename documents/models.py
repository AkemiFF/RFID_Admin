import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField
from identites.models import Personne, Entreprise, Utilisateur


class DocumentIdentite(models.Model):
    TYPE_DOCUMENT_CHOICES = [
        ('CNI_RECTO', 'CNI Recto'),
        ('CNI_VERSO', 'CNI Verso'),
        ('PASSEPORT', 'Passeport'),
        ('PERMIS_RECTO', 'Permis Recto'),
        ('PERMIS_VERSO', 'Permis Verso'),
        ('JUSTIFICATIF_DOMICILE', 'Justificatif de domicile'),
        ('PHOTO_IDENTITE', 'Photo d\'identité'),
    ]
    
    STATUT_VERIFICATION_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VERIFIE', 'Vérifié'),
        ('REJETE', 'Rejeté'),
        ('EXPIRE', 'Expiré'),
    ]
    
    NIVEAU_CONFIDENTIALITE_CHOICES = [
        ('PUBLIC', 'Public'),
        ('INTERNE', 'Interne'),
        ('CONFIDENTIEL', 'Confidentiel'),
        ('SECRET', 'Secret'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personne = models.ForeignKey(Personne, on_delete=models.CASCADE, null=True, blank=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, null=True, blank=True)
    type_document = models.CharField(max_length=50, choices=TYPE_DOCUMENT_CHOICES)
    nom_fichier = models.CharField(max_length=255)
    chemin_fichier = models.TextField()
    taille_fichier = models.BigIntegerField()
    type_mime = models.CharField(max_length=100)
    hash_fichier = models.CharField(max_length=255, unique=True)
    statut_verification = models.CharField(max_length=20, choices=STATUT_VERIFICATION_CHOICES, default='EN_ATTENTE')
    agent_verificateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    commentaire_verification = models.TextField(blank=True)
    date_expiration_document = models.DateField(null=True, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)
    date_verification = models.DateTimeField(null=True, blank=True)
    donnees_ocr = JSONField(default=dict, blank=True)
    niveau_confidentialite = models.CharField(max_length=20, choices=NIVEAU_CONFIDENTIALITE_CHOICES, default='INTERNE')

    class Meta:
        db_table = 'documents_identite'
        verbose_name = 'Document d\'identité'
        verbose_name_plural = 'Documents d\'identité'

    def __str__(self):
        return f"{self.type_document} - {self.nom_fichier}"
