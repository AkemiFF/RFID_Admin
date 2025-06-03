import uuid
from django.db import models
from django.db.models import JSONField
from cartes.models import CarteRFID
from identites.models import Utilisateur


class Transaction(models.Model):
    TYPE_TRANSACTION_CHOICES = [
        ('ACHAT', 'Achat'),
        ('RETRAIT', 'Retrait'),
        ('RECHARGE', 'Recharge'),
        ('TRANSFERT', 'Transfert'),
    ]
    
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('VALIDEE', 'Validée'),
        ('ECHOUEE', 'Échouée'),
        ('ANNULEE', 'Annulée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carte = models.ForeignKey(CarteRFID, on_delete=models.CASCADE)
    type_transaction = models.CharField(max_length=20, choices=TYPE_TRANSACTION_CHOICES)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    solde_avant = models.DecimalField(max_digits=15, decimal_places=2)
    carte_receipt = models.ForeignKey(CarteRFID, on_delete=models.CASCADE, related_name='transactions_client', null=True, blank=True)
    solde_apres = models.DecimalField(max_digits=15, decimal_places=2)
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_nom = models.CharField(max_length=255, blank=True, null=True)
    terminal_id = models.CharField(max_length=100, blank=True, null=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    reference_interne = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=100, blank=True)
    localisation = models.CharField(max_length=255, blank=True, null=True)
    coordonnees_gps = models.CharField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_COURS')
    code_erreur = models.CharField(max_length=50, blank=True, null=True)
    message_erreur = models.TextField(blank=True, null=True)
    frais_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taux_change = models.DecimalField(max_digits=10, decimal_places=6, default=1)
    devise = models.CharField(max_length=3, default='Ar')
    date_transaction = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    agent_validateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    donnees_brutes = JSONField(default=dict, blank=True, null=True)
    signature_transaction = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def __str__(self):
        return f"Transaction {self.reference_interne}"


class Rechargement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CARTE_BANCAIRE', 'Carte bancaire'),
        ('VIREMENT', 'Virement'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]
    
    STATUT_PAIEMENT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRME', 'Confirmé'),
        ('ECHEC', 'Échec'),
        ('REMBOURSE', 'Remboursé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    carte = models.ForeignKey(CarteRFID, on_delete=models.CASCADE)
    montant_recharge = models.DecimalField(max_digits=15, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES)
    reference_paiement = models.CharField(max_length=100, blank=True)
    operateur_mobile = models.CharField(max_length=50, blank=True)
    numero_mobile = models.CharField(max_length=20, blank=True)
    banque_emettrice = models.CharField(max_length=100, blank=True)
    numero_compte = models.CharField(max_length=50, blank=True)
    effectue_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='rechargements_effectues')
    agent_operateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='rechargements_operes')
    point_recharge = models.CharField(max_length=255)
    commission_prelevee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut_paiement = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='EN_ATTENTE')
    date_rechargement = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    recu_numero = models.CharField(max_length=100, unique=True)
    donnees_paiement = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'rechargements'
        verbose_name = 'Rechargement'
        verbose_name_plural = 'Rechargements'

    def __str__(self):
        return f"Rechargement {self.recu_numero}"
