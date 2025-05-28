import logging

from django.contrib.auth import logout
from django.db.models import Q
from django.utils import timezone
from identites.models import Utilisateur
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .models import LoginAttempt, Permission, Role, UserRole
from .permissions import HasPermission
from .serializers import (ChangePasswordSerializer,
                          CustomTokenObtainPairSerializer,
                          PermissionSerializer, RoleSerializer,
                          UserRoleSerializer, UserSerializer)

logger = logging.getLogger('authentication')


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'authentification JWT via email + logging"""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        email = request.data.get('email', '')

        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Connexion réussie, on récupère par email
                try:
                    user = Utilisateur.objects.get(email=email)
                    LoginAttempt.objects.create(
                        username=email,
                        user=user,
                        attempt_type='SUCCESS',
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    logger.info(f"Connexion réussie pour {email} depuis {ip_address}")
                except Utilisateur.DoesNotExist:
                    pass

            return response

        except Exception as e:
            # Connexion échouée
            LoginAttempt.objects.create(
                username=email,
                attempt_type='FAILED_PASSWORD',
                ip_address=ip_address,
                user_agent=user_agent,
                additional_info={'error': str(e)}
            )
            logger.warning(f"Tentative de connexion échouée pour {email} depuis {ip_address}")
            raise

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class LogoutView(generics.GenericAPIView):
    """Vue pour la déconnexion"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info(f"Déconnexion de l'utilisateur {request.user.username}")
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {str(e)}")
            return Response({"error": "Erreur lors de la déconnexion"}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """Vue pour changer le mot de passe"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Ancien mot de passe incorrect"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.force_changement_mdp = False
        user.save()

        logger.info(f"Mot de passe changé pour l'utilisateur {user.username}")
        return Response({"message": "Mot de passe changé avec succès"}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour le profil utilisateur"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    """Récupère les permissions de l'utilisateur connecté"""
    permissions = CustomTokenObtainPairSerializer.get_user_permissions(request.user)
    return Response({"permissions": permissions})


class PermissionViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des permissions"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'SYSTEM.READ'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'SYSTEM.UPDATE'
        return super().get_permissions()


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rôles"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'SYSTEM.READ'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'SYSTEM.UPDATE'
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system_role:
            return Response(
                {"error": "Impossible de supprimer un rôle système"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def assign_to_user(self, request, pk=None):
        """Assigner un rôle à un utilisateur"""
        role = self.get_object()
        user_id = request.data.get('user_id')
        context = request.data.get('context', {})

        try:
            user = Utilisateur.objects.get(id=user_id)
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'context': context,
                    'assigned_by': request.user
                }
            )
            
            if not created:
                user_role.context = context
                user_role.is_active = True
                user_role.save()

            return Response({"message": "Rôle assigné avec succès"})
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rôles utilisateurs"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'SYSTEM.READ'

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        role_id = self.request.query_params.get('role_id')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
            
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permission = 'SYSTEM.UPDATE'
        return super().get_permissions()
