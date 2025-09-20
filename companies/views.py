"""
Views y ViewSets para la aplicación de empresas.

Este módulo contiene las vistas de Django REST Framework para manejar
las operaciones CRUD de empresas, entidades y usuarios.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .models import Company, Entity, EntityType, User
from .serializers import CompanySerializer, EntitySerializer, EntityTypeSerializer, UserSerializer

logger = logging.getLogger(__name__)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar empresas.
    
    Proporciona operaciones CRUD para empresas y estadísticas relacionadas.
    """
    
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo las empresas a las que el usuario tiene acceso."""
        user = self.request.user
        if user.is_staff:
            return Company.objects.all()
        else:
            return Company.objects.filter(id=user.company.id)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Obtiene los usuarios de una empresa."""
        company = self.get_object()
        users = User.objects.filter(company=company, is_active=True)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def entities(self, request, pk=None):
        """Obtiene las entidades de una empresa."""
        company = self.get_object()
        entities = Entity.objects.filter(company=company, is_active=True)
        serializer = EntitySerializer(entities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtiene estadísticas de una empresa."""
        company = self.get_object()
        
        stats = {
            'users_count': company.get_active_users_count(),
            'documents_count': company.get_documents_count(),
            'entities_count': company.entities.filter(is_active=True).count(),
            'pending_documents_count': company.documents.filter(validation_status='P').count(),
            'approved_documents_count': company.documents.filter(validation_status='A').count(),
            'rejected_documents_count': company.documents.filter(validation_status='R').count(),
        }
        
        return Response(stats)


class EntityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para tipos de entidades.
    
    Los tipos de entidades son configurados por el administrador del sistema
    y no pueden ser modificados por usuarios regulares.
    """
    
    serializer_class = EntityTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo los tipos de entidades activos."""
        return EntityType.objects.filter(is_active=True)


class EntityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar entidades de negocio.
    
    Proporciona operaciones CRUD para entidades asociadas a empresas.
    """
    
    serializer_class = EntitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo las entidades de la empresa del usuario autenticado."""
        user = self.request.user
        return Entity.objects.filter(company=user.company).select_related(
            'entity_type', 'company'
        )
    
    def perform_create(self, serializer):
        """Asocia la entidad a la empresa del usuario autenticado."""
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Obtiene los documentos de una entidad."""
        entity = self.get_object()
        documents = entity.documents.all()
        
        # Importar aquí para evitar importaciones circulares
        from documents.serializers import DocumentSerializer
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtiene estadísticas de una entidad."""
        entity = self.get_object()
        
        stats = {
            'documents_count': entity.get_documents_count(),
            'pending_documents_count': entity.get_pending_documents_count(),
            'approved_documents_count': entity.documents.filter(validation_status='A').count(),
            'rejected_documents_count': entity.documents.filter(validation_status='R').count(),
        }
        
        return Response(stats)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios.
    
    Proporciona operaciones CRUD para usuarios de empresas.
    """
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo los usuarios de la empresa del usuario autenticado."""
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        else:
            return User.objects.filter(company=user.company)
    
    def perform_create(self, serializer):
        """Asocia el usuario a la empresa del usuario autenticado."""
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Cambia la contraseña de un usuario."""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': 'Nueva contraseña requerida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Contraseña cambiada exitosamente'})
    
    @action(detail=True, methods=['post'])
    def toggle_admin(self, request, pk=None):
        """Activa/desactiva el estado de administrador de empresa de un usuario."""
        user = self.get_object()
        
        # Solo los administradores de empresa pueden cambiar este estado
        if not request.user.is_company_admin and not request.user.is_staff:
            return Response(
                {'error': 'No tiene permisos para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_company_admin = not user.is_company_admin
        user.save()
        
        status_text = 'activado' if user.is_company_admin else 'desactivado'
        return Response({
            'message': f'Estado de administrador {status_text} exitosamente',
            'is_company_admin': user.is_company_admin
        })
    
    @action(detail=True, methods=['get'])
    def approval_stats(self, request, pk=None):
        """Obtiene estadísticas de aprobaciones de un usuario."""
        user = self.get_object()
        
        # Importar aquí para evitar importaciones circulares
        from documents.validation_service import ValidationService
        stats = ValidationService.get_user_approval_stats(user)
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def pending_approvals(self, request, pk=None):
        """Obtiene los documentos pendientes de aprobación de un usuario."""
        user = self.get_object()
        
        # Importar aquí para evitar importaciones circulares
        from documents.validation_service import ValidationService
        pending_documents = ValidationService.get_pending_approvals_for_user(user)
        
        from documents.serializers import DocumentSerializer
        serializer = DocumentSerializer(pending_documents, many=True)
        return Response(serializer.data)
