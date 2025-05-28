import logging

from cartes.models import CarteRFID
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from identites.models import Utilisateur
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import LoginAttempt, Permission, Role, UserRole

User = get_user_model()

logger = logging.getLogger('authentication')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour l'authentification JWT via email ou carte RFID"""
    username_field = 'email'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remplacer username par email
        self.fields.pop('username', None)
        self.fields['email'] = serializers.EmailField()
        self.fields['password'] = serializers.CharField(write_only=True)
        self.fields['card_number'] = serializers.CharField(required=False)
        self.fields['remember_me'] = serializers.BooleanField(default=False)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['role'] = user.role
        token['permissions'] = cls.get_user_permissions(user)
        token['is_admin'] = user.role in ['ADMIN', 'SUPERVISEUR']
        return token

    @staticmethod
    def get_user_permissions(user):
        """Récupère les permissions de l'utilisateur"""
        permissions = []
        user_roles = user.user_roles.filter(is_active=True)
        for user_role in user_roles:
            for perm in user_role.role.permissions.filter(is_active=True):
                permissions.append(f"{perm.resource_type}.{perm.action_type}")
        return list(set(permissions))

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        card_number = attrs.get('card_number')
        user = None

        if card_number:
            # Authentification par carte RFID
            try:
                carte = CarteRFID.objects.get(numero_carte=card_number, statut='ACTIVE')
                user = carte.proprietaire
                if not user or not user.actif:
                    raise serializers.ValidationError('Carte non associée à un utilisateur actif.')
            except CarteRFID.DoesNotExist:
                raise serializers.ValidationError('Numéro de carte invalide.')
        else:
            attrs['username'] = email
            print(email)
            print(password)
            user = User.objects.get(email=email)
            print(user)
            if not user.check_password(password):
                raise serializers.ValidationError('Email ou mot de passe invalide.')

        # Vérifier statut du compte
        if not user.actif:
            raise serializers.ValidationError('Compte désactivé.')
        if user.compte_verrouille_jusqu and user.compte_verrouille_jusqu > timezone.now():
            raise serializers.ValidationError('Compte temporairement verrouillé.')

        # Mise à jour des logs utilisateur
        user.derniere_connexion = timezone.now()
        user.tentatives_connexion_echouees = 0
        user.save()

        # Logging de la tentative
        try:
            LoginAttempt.objects.create(
                username=user.email,
                user=user,
                attempt_type='SUCCESS',
                ip_address=self.context['request'].META.get('REMOTE_ADDR'),
                user_agent=self.context['request'].META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            logger.warning('Erreur lors de l\'enregistrement de la tentative réussie pour %s', user.email)

        refresh = self.get_token(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur"""
    permissions = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'region_assignee', 'actif', 'derniere_connexion',
            'permissions', 'roles'
        ]

    def get_permissions(self, obj):
        return CustomTokenObtainPairSerializer.get_user_permissions(obj)

    def get_roles(self, obj):
        user_roles = UserRole.objects.filter(user=obj, is_active=True)
        return [{'name': ur.role.name, 'context': ur.context} for ur in user_roles]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Role
        fields = '__all__'

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
        
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserRole
        fields = '__all__'
