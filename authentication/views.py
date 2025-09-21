"""
Views de autenticación para la API REST.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from companies.models import User
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint de login para obtener token de autenticación.
    
    POST /api/auth/login/
    {
        "username": "usuario",
        "password": "contraseña"
    }
    
    Respuesta:
    {
        "token": "token_aqui",
        "user": {
            "id": "uuid",
            "username": "usuario",
            "email": "email@example.com",
            "company": {
                "id": "uuid",
                "name": "Empresa"
            }
        }
    }
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username y password son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is None or user.is_anonymous:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generar token simple (en producción usar JWT)
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(user)
        
        # Preparar respuesta
        user_data = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'company': {
                'id': str(user.company.id),
                'name': user.company.name
            } if user.company else None
        }
        
        return Response({
            'token': f"{user.id}:{token}",
            'user': user_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    Endpoint de logout.
    
    POST /api/auth/logout/
    Headers: Authorization: Token token_aqui
    """
    return Response({
        'message': 'Logout exitoso'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def profile(request):
    """
    Obtener perfil del usuario autenticado.
    
    GET /api/auth/profile/
    Headers: Authorization: Token token_aqui
    """
    user = request.user
    
    if user.is_anonymous:
        return Response({
            'error': 'Usuario no autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user_data = {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'company': {
            'id': str(user.company.id),
            'name': user.company.name
        } if user.company else None
    }
    
    return Response(user_data, status=status.HTTP_200_OK)
