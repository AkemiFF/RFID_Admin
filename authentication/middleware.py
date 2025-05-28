from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger('authentication')


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware pour l'authentification JWT automatique"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()
        super().__init__(get_response)

    def process_request(self, request):
        # Ignorer les URLs qui n'ont pas besoin d'authentification
        exempt_urls = [
            '/admin/',
            '/api/auth/login/',
            '/api/auth/refresh/',
            '/api/auth/register/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(url) for url in exempt_urls):
            return None

        # Tenter l'authentification JWT
        try:
            auth_result = self.jwt_authentication.authenticate(request)
            if auth_result:
                user, token = auth_result
                request.user = user
                request.auth = token
                logger.debug(f"Utilisateur authentifié: {user.username}")
            else:
                request.user = AnonymousUser()
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token JWT invalide: {str(e)}")
            request.user = AnonymousUser()
        except Exception as e:
            logger.error(f"Erreur d'authentification JWT: {str(e)}")
            request.user = AnonymousUser()

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware pour ajouter des en-têtes de sécurité"""
    
    def process_response(self, request, response):
        # Ajouter des en-têtes de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP pour les API
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'"
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware simple pour la limitation de taux"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        super().__init__(get_response)

    def process_request(self, request):
        # Limitation simple basée sur l'IP
        ip_address = self.get_client_ip(request)
        
        # Réinitialiser le compteur toutes les minutes (simplification)
        import time
        current_minute = int(time.time() // 60)
        
        if ip_address not in self.request_counts:
            self.request_counts[ip_address] = {'minute': current_minute, 'count': 0}
        
        if self.request_counts[ip_address]['minute'] != current_minute:
            self.request_counts[ip_address] = {'minute': current_minute, 'count': 0}
        
        self.request_counts[ip_address]['count'] += 1
        
        # Limite de 100 requêtes par minute par IP
        if self.request_counts[ip_address]['count'] > 100:
            logger.warning(f"Rate limit dépassé pour l'IP {ip_address}")
            return JsonResponse(
                {'error': 'Trop de requêtes. Veuillez réessayer plus tard.'}, 
                status=429
            )
        
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
