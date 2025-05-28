import uuid
from django.db import models
from identites.models import Utilisateur


class ParametreSysteme(models.Model):
    TYPE_VALEUR_CHOICES = [
        ('STRING', 'Chaîne'),
        ('INTEGER', 'Entier'),
        ('DECIMAL', 'Décimal'),
        ('BOOLEAN', 'Booléen'),
        ('JSON', 'JSON'),
        ('DATE', 'Date'),
        ('DATETIME', 'Date et heure'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cle = models.CharField(max_length=255, unique=True)
    valeur = models.TextField()
    type_valeur = models.CharField(max_length=20, choices=TYPE_VALEUR_CHOICES)
    categorie = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    valeur_par_defaut = models.TextField(blank=True)
    modifiable = models.BooleanField(default=True)
    visible_interface = models.BooleanField(default=True)
    validation_regex = models.CharField(max_length=500, blank=True)
    valeur_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    valeur_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'parametres_systeme'
        verbose_name = 'Paramètre Système'
        verbose_name_plural = 'Paramètres Système'

    def __str__(self):
        return f"{self.cle} = {self.valeur}"
