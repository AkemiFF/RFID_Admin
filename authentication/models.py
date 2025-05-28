import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from identites.models import Utilisateur


class RefreshToken(models.Model):
    """Modèle pour gérer les refresh tokens JWT"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_blacklisted = models.BooleanField(default=False)
    device_info = JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'auth_refresh_tokens'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'
        indexes = [
            models.Index(fields=['user', 'is_blacklisted']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Token for {self.user.username} - {self.created_at}"


class LoginAttempt(models.Model):
    """Modèle pour traquer les tentatives de connexion"""
    ATTEMPT_TYPES = [
        ('SUCCESS', 'Succès'),
        ('FAILED_PASSWORD', 'Mot de passe incorrect'),
        ('FAILED_USER', 'Utilisateur inexistant'),
        ('BLOCKED', 'Compte bloqué'),
        ('EXPIRED', 'Compte expiré'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150)
    user = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_info = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'auth_login_attempts'
        verbose_name = 'Tentative de connexion'
        verbose_name_plural = 'Tentatives de connexion'
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['attempt_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.username} - {self.attempt_type} - {self.timestamp}"


class Permission(models.Model):
    """Modèle pour les permissions personnalisées"""
    RESOURCE_TYPES = [
        ('CARTES', 'Cartes'),
        ('TRANSACTIONS', 'Transactions'),
        ('IDENTITES', 'Identités'),
        ('DOCUMENTS', 'Documents'),
        ('LOGS', 'Logs'),
        ('NOTIFICATIONS', 'Notifications'),
        ('PARAMETRES', 'Paramètres'),
        ('API_MANAGEMENT', 'Gestion API'),
        ('RAPPORTS', 'Rapports'),
        ('SYSTEM', 'Système'),
    ]

    ACTION_TYPES = [
        ('CREATE', 'Créer'),
        ('READ', 'Lire'),
        ('UPDATE', 'Modifier'),
        ('DELETE', 'Supprimer'),
        ('EXPORT', 'Exporter'),
        ('IMPORT', 'Importer'),
        ('APPROVE', 'Approuver'),
        ('REJECT', 'Rejeter'),
        ('BLOCK', 'Bloquer'),
        ('UNBLOCK', 'Débloquer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    conditions = JSONField(default=dict, blank=True)  # Conditions supplémentaires
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        unique_together = ['resource_type', 'action_type']

    def __str__(self):
        return f"{self.name} ({self.resource_type}.{self.action_type})"


class Role(models.Model):
    """Modèle pour les rôles avec permissions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_system_role = models.BooleanField(default=False)  # Rôles système non modifiables
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'auth_roles'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'

    def __str__(self):
        return self.name

    def has_permission(self, resource_type, action_type):
        """Vérifie si le rôle a une permission spécifique"""
        return self.permissions.filter(
            resource_type=resource_type,
            action_type=action_type,
            is_active=True
        ).exists()


class UserRole(models.Model):
    """Modèle pour assigner des rôles aux utilisateurs avec contexte"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    context = JSONField(default=dict, blank=True)  # Contexte (région, département, etc.)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles')
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_user_roles'
        verbose_name = 'Rôle utilisateur'
        verbose_name_plural = 'Rôles utilisateurs'
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
