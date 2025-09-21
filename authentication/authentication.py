"""
Autenticación personalizada para la API.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator
from companies.models import User
import logging

logger = logging.getLogger(__name__)


class TokenAuthentication(BaseAuthentication):
    """
    Autenticación basada en token simple.
    """
    
    def authenticate(self, request):
        """
        Autentica al usuario basado en el token.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith('Token '):
            return None
        
        try:
            token = auth_header.split(' ')[1]
            user_id, token_value = token.split(':', 1)
            
            user = User.objects.get(id=user_id)
            
            # Verificar token
            if default_token_generator.check_token(user, token_value):
                return (user, token)
            else:
                raise AuthenticationFailed('Token inválido')
                
        except (ValueError, User.DoesNotExist, IndexError):
            raise AuthenticationFailed('Token inválido')
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            raise AuthenticationFailed('Error de autenticación')
    
    def authenticate_header(self, request):
        """
        Retorna el header de autenticación requerido.
        """
        return 'Token'
