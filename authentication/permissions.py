from rest_framework.permissions import BasePermission
from .models import UserRole


class HasPermission(BasePermission):
    """Permission personnalisée basée sur les rôles et permissions"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admin a tous les droits
        if request.user.role == 'ADMIN':
            return True

        # Vérifier la permission requise
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        return self.user_has_permission(request.user, required_permission)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admin a tous les droits
        if request.user.role == 'ADMIN':
            return True

        # Vérifier la permission requise
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        # Vérifier si l'utilisateur peut accéder à cet objet spécifique
        return self.user_has_object_permission(request.user, required_permission, obj)

    def user_has_permission(self, user, permission):
        """Vérifie si l'utilisateur a une permission spécifique"""
        try:
            resource_type, action_type = permission.split('.')
        except ValueError:
            return False

        # Récupérer les rôles actifs de l'utilisateur
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        
        for user_role in user_roles:
            if user_role.role.has_permission(resource_type, action_type):
                return True

        return False

    def user_has_object_permission(self, user, permission, obj):
        """Vérifie si l'utilisateur a une permission sur un objet spécifique"""
        # Logique de base : même que la permission générale
        # Peut être étendue pour des vérifications spécifiques à l'objet
        return self.user_has_permission(user, permission)


class IsOwnerOrAdmin(BasePermission):
    """Permission pour les propriétaires d'objets ou les admins"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin a tous les droits
        if request.user.role == 'ADMIN':
            return True

        # Vérifier si l'utilisateur est le propriétaire
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        if hasattr(obj, 'proprietaire') and obj.proprietaire == request.user:
            return True

        if hasattr(obj, 'cree_par') and obj.cree_par == request.user.id:
            return True

        return False


class IsAdminOrReadOnly(BasePermission):
    """Permission lecture pour tous, écriture pour les admins"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Écriture uniquement pour les admins
        return request.user.role in ['ADMIN', 'SUPERVISEUR']


class RegionPermission(BasePermission):
    """Permission basée sur la région assignée"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin a accès à toutes les régions
        if request.user.role == 'ADMIN':
            return True

        return True  # Vérification détaillée dans has_object_permission

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin a tous les droits
        if request.user.role == 'ADMIN':
            return True

        # Vérifier si l'objet a une région et si l'utilisateur y a accès
        if hasattr(obj, 'region') and request.user.region_assignee:
            return obj.region == request.user.region_assignee

        return True  # Par défaut, autoriser si pas de restriction régionale
