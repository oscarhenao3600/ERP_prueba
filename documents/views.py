"""
Views y ViewSets para la API del sistema ERP de gestión de documentos.

Este módulo contiene las vistas de Django REST Framework para manejar
las operaciones CRUD y acciones específicas del sistema de documentos.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from .models import Document, ValidationFlow, ValidationAction
from .serializers import (
    DocumentSerializer, DocumentCreateSerializer, DocumentApprovalSerializer,
    DocumentRejectionSerializer, DocumentUploadSerializer
)
from .services import storage_service
from .validation_service import ValidationService
from companies.models import Company, Entity, User

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar documentos.
    
    Proporciona operaciones CRUD para documentos y acciones específicas
    como aprobación, rechazo y descarga.
    """
    
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retorna solo los documentos de la empresa del usuario autenticado."""
        user = self.request.user
        return Document.objects.filter(company=user.company).select_related(
            'company', 'entity', 'created_by', 'validation_flow'
        ).prefetch_related('validation_flow__steps__approver')
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action == 'approve':
            return DocumentApprovalSerializer
        elif self.action == 'reject':
            return DocumentRejectionSerializer
        elif self.action == 'upload_url':
            return DocumentUploadSerializer
        return DocumentSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo documento con metadatos y opcionalmente un flujo de validación.
        
        Este endpoint no sube el archivo físicamente, solo crea el registro
        en la base de datos con los metadatos proporcionados.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Obtener la empresa y entidad
                company = Company.objects.get(id=serializer.validated_data['company_id'])
                entity_data = serializer.validated_data['entity']
                entity = Entity.objects.get(
                    company=company,
                    entity_type__name=entity_data['entity_type'],
                    external_id=entity_data['entity_id']
                )
                
                # Crear el documento
                document_data = serializer.validated_data['document']
                document = Document.objects.create(
                    company=company,
                    entity=entity,
                    name=document_data['name'],
                    mime_type=document_data['mime_type'],
                    size_bytes=document_data['size_bytes'],
                    bucket_key=document_data['bucket_key'],
                    file_hash=document_data.get('file_hash', ''),
                    description=document_data.get('description', ''),
                    tags=document_data.get('tags', []),
                    created_by=request.user
                )
                
                # Crear flujo de validación si se proporciona
                validation_flow_data = serializer.validated_data.get('validation_flow')
                if validation_flow_data and validation_flow_data.get('enabled', False):
                    ValidationService.create_validation_flow(
                        document, validation_flow_data['steps']
                    )
                
                # Serializar la respuesta
                response_serializer = DocumentSerializer(document)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error al crear documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def upload_url(self, request):
        """
        Genera una URL pre-firmada para subir un archivo al bucket.
        
        Este endpoint genera las URLs necesarias para que el cliente
        suba el archivo directamente al bucket de almacenamiento.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Obtener datos validados
            company_id = serializer.validated_data['company_id']
            entity_type = serializer.validated_data['entity_type']
            entity_id = serializer.validated_data['entity_id']
            filename = serializer.validated_data['filename']
            mime_type = serializer.validated_data['mime_type']
            size_bytes = serializer.validated_data['size_bytes']
            
            # Generar clave del bucket
            bucket_key = storage_service.generate_bucket_key(
                str(company_id), entity_type, entity_id, filename
            )
            
            # Generar URL pre-firmada
            presigned_data = storage_service.generate_presigned_upload_url(
                bucket_key, mime_type
            )
            
            return Response({
                'bucket_key': bucket_key,
                'upload_url': presigned_data['url'],
                'fields': presigned_data.get('fields', {}),
                'expires_in': storage_service.expiration
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al generar URL de subida: {e}")
            return Response(
                {'error': 'Error al generar URL de subida'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Genera una URL pre-firmada para descargar un documento.
        
        Retorna una URL pre-firmada que permite al cliente descargar
        el archivo directamente desde el bucket de almacenamiento.
        """
        document = self.get_object()
        
        try:
            # Verificar que el archivo existe en el bucket
            if not storage_service.file_exists(document.bucket_key):
                return Response(
                    {'error': 'Archivo no encontrado en el bucket'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generar URL pre-firmada
            download_url = storage_service.generate_presigned_download_url(
                document.bucket_key
            )
            
            return Response({
                'download_url': download_url,
                'filename': document.name,
                'mime_type': document.mime_type,
                'size_bytes': document.size_bytes,
                'expires_in': storage_service.expiration
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al generar URL de descarga: {e}")
            return Response(
                {'error': 'Error al generar URL de descarga'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Aprueba un documento siguiendo las reglas de jerarquía.
        
        Si el usuario que aprueba tiene mayor jerarquía, se aprueban
        automáticamente los pasos previos pendientes.
        """
        document = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Obtener el usuario actor
            actor = User.objects.get(id=serializer.validated_data['actor_user_id'])
            reason = serializer.validated_data.get('reason', '')
            
            # Aprobar el documento
            action = ValidationService.approve_document(document, actor, reason)
            
            # Serializar la respuesta
            response_serializer = DocumentSerializer(document)
            return Response({
                'message': 'Documento aprobado exitosamente',
                'document': response_serializer.data,
                'action_id': action.id
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al aprobar documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Rechaza un documento (acción terminal).
        
        Un rechazo marca el documento como rechazado y desactiva
        el flujo de validación.
        """
        document = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Obtener el usuario actor
            actor = User.objects.get(id=serializer.validated_data['actor_user_id'])
            reason = serializer.validated_data.get('reason', '')
            
            # Rechazar el documento
            action = ValidationService.reject_document(document, actor, reason)
            
            # Serializar la respuesta
            response_serializer = DocumentSerializer(document)
            return Response({
                'message': 'Documento rechazado exitosamente',
                'document': response_serializer.data,
                'action_id': action.id
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al rechazar documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def validation_status(self, request, pk=None):
        """
        Obtiene el estado detallado del flujo de validación de un documento.
        """
        document = self.get_object()
        
        try:
            status_info = ValidationService.get_validation_status(document)
            return Response(status_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener estado de validación: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """
        Obtiene los documentos pendientes de aprobación para el usuario autenticado.
        """
        try:
            pending_documents = ValidationService.get_pending_approvals_for_user(request.user)
            serializer = DocumentSerializer(pending_documents, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener documentos pendientes: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def approval_stats(self, request):
        """
        Obtiene estadísticas de aprobaciones para el usuario autenticado.
        """
        try:
            stats = ValidationService.get_user_approval_stats(request.user)
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        Elimina un documento y su archivo del bucket.
        
        Esta acción elimina tanto el registro de la base de datos
        como el archivo físico del bucket de almacenamiento.
        """
        document = self.get_object()
        
        try:
            with transaction.atomic():
                # Eliminar el archivo del bucket
                storage_service.delete_file(document.bucket_key)
                
                # Eliminar el documento de la base de datos
                document.delete()
                
                return Response(
                    {'message': 'Documento eliminado exitosamente'},
                    status=status.HTTP_204_NO_CONTENT
                )
                
        except Exception as e:
            logger.error(f"Error al eliminar documento: {e}")
            return Response(
                {'error': 'Error al eliminar documento'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
