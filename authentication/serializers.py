from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from identites.models import Utilisateur
from .models import Permission, Role, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour l'authentification JWT"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField()
        self.fields['password'] = serializers.CharField()
        self.fields['card_number'] = serializers.CharField(required=False)
        self.fields['remember_me'] = serializers.BooleanField(default=False)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Ajouter des informations personnalisées au token
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['role'] = user.role
        token['permissions'] = cls.get_user_permissions(user)
        token['is_admin'] = user.role in ['ADMIN', 'SUPERVISEUR']
        
        return token

    @staticmethod
    def get_user_permissions(user):
        """Récupère les permissions de l'utilisateur"""
        permissions = []
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        
        for user_role in user_roles:
            role_permissions = user_role.role.permissions.filter(is_active=True)
            for perm in role_permissions:
                permissions.append(f"{perm.resource_type}.{perm.action_type}")
        
        return list(set(permissions))  # Supprimer les doublons

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        card_number = attrs.get('card_number')

        if card_number:
            # Authentification par carte RFID
            try:
                from cartes.models import Carte
                carte = Carte.objects.get(numero_carte=card_number, statut='ACTIVE')
                user = carte.proprietaire
                if not user or not user.is_active:
                    raise serializers.ValidationError('Carte non associée à un utilisateur actif.')
            except Carte.DoesNotExist:
                raise serializers.ValidationError('Numéro de carte invalide.')
        else:
            # Authentification classique
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides.')

        if not user.actif:
            raise serializers.ValidationError('Compte désactivé.')

        # Vérifier si le compte est verrouillé
        if user.compte_verrouille_jusqu and user.compte_verrouille_jusqu > timezone.now():
            raise serializers.ValidationError('Compte temporairement verrouillé.')

        # Mettre à jour la dernière connexion
        user.derniere_connexion = timezone.now()
        user.tentatives_connexion_echouees = 0
        user.save()

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
