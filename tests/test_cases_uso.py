"""
Pruebas específicas para casos de uso del sistema ERP de gestión de documentos.

Este módulo contiene pruebas detalladas para los casos de uso principales,
incluyendo flujos completos de subida, validación jerárquica y manejo de errores.
"""

import json
import uuid
from unittest.mock import patch, Mock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token

from companies.models import Company, EntityType, Entity, User
from documents.models import Document, ValidationFlow, ValidationStep, ValidationAction

User = get_user_model()


class DocumentUploadFlowTestCase(APITestCase):
    """
    Casos de prueba para el flujo completo de subida de documentos.
    
    Cubre:
    - Generación de URL pre-firmada
    - Creación de documento con metadatos
    - Validación de datos
    - Manejo de errores
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de flujo de subida."""
        self.company = Company.objects.create(
            name="Empresa Test Upload",
            legal_name="Empresa Test Upload S.A.S.",
            tax_id="900123456-1",
            email="upload@test.com"
        )
        
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id="VEH001",
            name="Vehículo Test Upload"
        )
        
        self.user = User.objects.create_user(
            username="upload_user",
            email="upload@test.com",
            password="testpass123",
            company=self.company
        )
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    @patch('documents.services.storage_service')
    def test_complete_upload_flow_with_validation(self, mock_storage):
        """
        Prueba el flujo completo de subida con validación jerárquica.
        
        Casos cubiertos:
        - Generación de URL pre-firmada
        - Creación de documento con metadatos
        - Configuración de flujo de validación
        - Verificación de estados
        """
        # Mock de respuesta del servicio de storage
        mock_storage.generate_presigned_upload_url.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/upload-url',
            'fields': {'Content-Type': 'application/pdf'}
        }
        
        # Paso 1: Generar URL de subida
        upload_data = {
            "company_id": str(self.company.id),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "soat.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 123456
        }
        
        response = self.client.post('/api/documents/upload_url/', upload_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('upload_url', response.data)
        self.assertIn('bucket_key', response.data)
        
        bucket_key = response.data['bucket_key']
        
        # Paso 2: Crear documento con flujo de validación
        document_data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "soat.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 123456,
                "bucket_key": bucket_key,
                "description": "SOAT del vehículo",
                "tags": ["seguro", "vehiculo", "soat"]
            },
            "validation_flow": {
                "enabled": True,
                "steps": [
                    {"order": 1, "approver_user_id": str(self.user.id)}
                ]
            }
        }
        
        response = self.client.post('/api/documents/', document_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el documento fue creado correctamente
        document = Document.objects.get(name="soat.pdf")
        self.assertEqual(document.company, self.company)
        self.assertEqual(document.entity, self.entity)
        self.assertEqual(document.mime_type, "application/pdf")
        self.assertEqual(document.size_bytes, 123456)
        self.assertEqual(document.description, "SOAT del vehículo")
        self.assertEqual(document.tags, ["seguro", "vehiculo", "soat"])
        self.assertEqual(document.validation_status, 'P')
        
        # Verificar que se creó el flujo de validación
        validation_flow = document.validation_flow
        self.assertTrue(validation_flow.is_active)
        self.assertEqual(validation_flow.steps.count(), 1)
        
        step = validation_flow.steps.first()
        self.assertEqual(step.order, 1)
        self.assertEqual(step.approver, self.user)
        self.assertEqual(step.status, 'P')
    
    @patch('documents.services.storage_service')
    def test_upload_flow_without_validation(self, mock_storage):
        """
        Prueba el flujo de subida sin flujo de validación.
        
        Casos cubiertos:
        - Creación de documento simple
        - Sin estado de validación
        - Metadatos básicos
        """
        mock_storage.generate_presigned_upload_url.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/upload-url',
            'fields': {'Content-Type': 'application/pdf'}
        }
        
        # Generar URL de subida
        upload_data = {
            "company_id": str(self.company.id),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "manual.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 98765
        }
        
        response = self.client.post('/api/documents/upload_url/', upload_data, format='json')
        bucket_key = response.data['bucket_key']
        
        # Crear documento sin validación
        document_data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "manual.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 98765,
                "bucket_key": bucket_key,
                "description": "Manual del vehículo"
            }
        }
        
        response = self.client.post('/api/documents/', document_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar documento sin validación
        document = Document.objects.get(name="manual.pdf")
        self.assertIsNone(document.validation_status)
        self.assertFalse(hasattr(document, 'validation_flow'))
    
    def test_upload_flow_invalid_data(self):
        """
        Prueba el manejo de datos inválidos en el flujo de subida.
        
        Casos cubiertos:
        - Tipo MIME no permitido
        - Tamaño de archivo excesivo
        - Empresa inexistente
        - Entidad inexistente
        """
        # Tipo MIME no permitido
        invalid_data = {
            "company_id": str(self.company.id),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "virus.exe",
            "mime_type": "application/x-executable",
            "size_bytes": 1024
        }
        
        response = self.client.post('/api/documents/upload_url/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Tamaño excesivo
        invalid_data = {
            "company_id": str(self.company.id),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "huge.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 50000000  # 50MB
        }
        
        response = self.client.post('/api/documents/upload_url/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Empresa inexistente
        invalid_data = {
            "company_id": str(uuid.uuid4()),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "test.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024
        }
        
        response = self.client.post('/api/documents/upload_url/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HierarchicalValidationTestCase(APITestCase):
    """
    Casos de prueba para la validación jerárquica de documentos.
    
    Cubre:
    - Aprobación automática de pasos previos
    - Rechazo terminal
    - Validación de permisos
    - Estados de validación
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de validación jerárquica."""
        self.company = Company.objects.create(
            name="Empresa Test Validation",
            legal_name="Empresa Test Validation S.A.S.",
            tax_id="900123456-2",
            email="validation@test.com"
        )
        
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id="VEH002",
            name="Vehículo Test Validation"
        )
        
        # Crear usuarios con diferentes roles
        self.user1 = User.objects.create_user(
            username="approver1",
            email="approver1@test.com",
            password="testpass123",
            company=self.company,
            first_name="Aprobador",
            last_name="Uno"
        )
        
        self.user2 = User.objects.create_user(
            username="approver2",
            email="approver2@test.com",
            password="testpass123",
            company=self.company,
            first_name="Aprobador",
            last_name="Dos"
        )
        
        self.user3 = User.objects.create_user(
            username="approver3",
            email="approver3@test.com",
            password="testpass123",
            company=self.company,
            first_name="Aprobador",
            last_name="Tres"
        )
        
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@test.com",
            password="testpass123",
            company=self.company
        )
        
        # Crear documento con flujo de validación
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="validation_test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/validation_test.pdf",
            created_by=self.creator,
            validation_status='P'
        )
        
        # Crear flujo de validación jerárquico
        self.validation_flow = ValidationFlow.objects.create(
            document=self.document
        )
        
        # Crear pasos de validación
        self.step1 = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user1
        )
        
        self.step2 = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=2,
            approver=self.user2
        )
        
        self.step3 = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=3,
            approver=self.user3
        )
    
    def test_hierarchical_approval_flow(self):
        """
        Prueba el flujo de aprobación jerárquico completo.
        
        Casos cubiertos:
        - Aprobación por usuario de orden intermedio
        - Aprobación automática de pasos previos
        - Aprobación por usuario de mayor jerarquía
        - Completado del flujo
        """
        # Autenticar como usuario de orden 2
        token = Token.objects.create(user=self.user2)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Paso 1: Aprobar con usuario de orden 2
        approval_data = {
            "actor_user_id": str(self.user2.id),
            "reason": "Documento cumple con requisitos de nivel 2"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se aprobaron automáticamente los pasos previos
        self.step1.refresh_from_db()
        self.step2.refresh_from_db()
        self.step3.refresh_from_db()
        
        self.assertEqual(self.step1.status, 'A')  # Aprobado automáticamente
        self.assertEqual(self.step2.status, 'A')  # Aprobado por el usuario
        self.assertEqual(self.step3.status, 'P')  # Sigue pendiente
        
        # Verificar que el documento sigue pendiente
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'P')
        
        # Verificar que se creó la acción de validación
        action = ValidationAction.objects.filter(
            document=self.document,
            actor=self.user2
        ).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.action, 'A')
        self.assertEqual(action.reason, "Documento cumple con requisitos de nivel 2")
        
        # Paso 2: Aprobar con usuario de orden 3 (mayor jerarquía)
        token = Token.objects.create(user=self.user3)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        approval_data = {
            "actor_user_id": str(self.user3.id),
            "reason": "Documento aprobado por máxima autoridad"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el documento está completamente aprobado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'A')
        
        # Verificar que todos los pasos están aprobados
        self.step1.refresh_from_db()
        self.step2.refresh_from_db()
        self.step3.refresh_from_db()
        
        self.assertEqual(self.step1.status, 'A')
        self.assertEqual(self.step2.status, 'A')
        self.assertEqual(self.step3.status, 'A')
    
    def test_terminal_rejection_flow(self):
        """
        Prueba el flujo de rechazo terminal.
        
        Casos cubiertos:
        - Rechazo por cualquier aprobador
        - Marcado como rechazado
        - Desactivación del flujo
        - Bloqueo de nuevas acciones
        """
        # Autenticar como usuario de orden 1
        token = Token.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Rechazar documento
        rejection_data = {
            "actor_user_id": str(self.user1.id),
            "reason": "Documento no cumple con los estándares requeridos"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/reject/',
            rejection_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el documento está rechazado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'R')
        
        # Verificar que el paso fue rechazado
        self.step1.refresh_from_db()
        self.assertEqual(self.step1.status, 'R')
        
        # Verificar que el flujo fue desactivado
        self.validation_flow.refresh_from_db()
        self.assertFalse(self.validation_flow.is_active)
        
        # Verificar que se creó la acción de rechazo
        action = ValidationAction.objects.filter(
            document=self.document,
            actor=self.user1
        ).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.action, 'R')
        self.assertEqual(action.reason, "Documento no cumple con los estándares requeridos")
        
        # Intentar aprobar después del rechazo (debe fallar)
        approval_data = {
            "actor_user_id": str(self.user2.id),
            "reason": "Intento de aprobación después del rechazo"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_approval_permissions(self):
        """
        Prueba la validación de permisos para aprobación.
        
        Casos cubiertos:
        - Usuario no aprobador
        - Usuario de otra empresa
        - Usuario sin permisos
        """
        # Crear usuario de otra empresa
        other_company = Company.objects.create(
            name="Otra Empresa",
            legal_name="Otra Empresa S.A.S.",
            tax_id="900123456-3",
            email="otra@empresa.com"
        )
        
        other_user = User.objects.create_user(
            username="other_user",
            email="other@test.com",
            password="testpass123",
            company=other_company
        )
        
        # Autenticar como usuario de otra empresa
        token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Intentar aprobar documento de otra empresa
        approval_data = {
            "actor_user_id": str(other_user.id),
            "reason": "Intento de aprobación no autorizado"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Autenticar como creador del documento (no es aprobador)
        token = Token.objects.create(user=self.creator)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Intentar aprobar como no aprobador
        approval_data = {
            "actor_user_id": str(self.creator.id),
            "reason": "Intento de aprobación sin permisos"
        }
        
        response = self.client.post(
            f'/api/documents/{self.document.id}/approve/',
            approval_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class DocumentDownloadTestCase(APITestCase):
    """
    Casos de prueba para la descarga de documentos.
    
    Cubre:
    - Generación de URLs pre-firmadas
    - Verificación de existencia de archivos
    - Manejo de errores
    - Validación de permisos
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de descarga."""
        self.company = Company.objects.create(
            name="Empresa Test Download",
            legal_name="Empresa Test Download S.A.S.",
            tax_id="900123456-4",
            email="download@test.com"
        )
        
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id="VEH003",
            name="Vehículo Test Download"
        )
        
        self.user = User.objects.create_user(
            username="download_user",
            email="download@test.com",
            password="testpass123",
            company=self.company
        )
        
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="download_test.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            bucket_key="test/download_test.pdf",
            created_by=self.user
        )
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    @patch('documents.services.storage_service')
    def test_successful_download(self, mock_storage):
        """
        Prueba la descarga exitosa de un documento.
        
        Casos cubiertos:
        - Archivo existe en bucket
        - Generación de URL pre-firmada
        - Metadatos correctos
        """
        # Mock de archivo existente
        mock_storage.file_exists.return_value = True
        mock_storage.generate_presigned_download_url.return_value = 'https://test-bucket.s3.amazonaws.com/download-url'
        
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        self.assertEqual(response.data['filename'], 'download_test.pdf')
        self.assertEqual(response.data['mime_type'], 'application/pdf')
        self.assertEqual(response.data['size_bytes'], 2048)
        self.assertIn('expires_in', response.data)
        
        # Verificar que se llamaron los métodos correctos
        mock_storage.file_exists.assert_called_once_with(self.document.bucket_key)
        mock_storage.generate_presigned_download_url.assert_called_once_with(self.document.bucket_key)
    
    @patch('documents.services.storage_service')
    def test_download_file_not_found(self, mock_storage):
        """
        Prueba el manejo cuando el archivo no existe en el bucket.
        
        Casos cubiertos:
        - Archivo no existe en bucket
        - Error 404 apropiado
        - Mensaje de error descriptivo
        """
        # Mock de archivo no encontrado
        mock_storage.file_exists.return_value = False
        
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Archivo no encontrado en el bucket')
    
    @patch('documents.services.storage_service')
    def test_download_storage_error(self, mock_storage):
        """
        Prueba el manejo de errores del servicio de storage.
        
        Casos cubiertos:
        - Error en servicio de storage
        - Error 500 apropiado
        - Logging de errores
        """
        # Mock de error en servicio
        mock_storage.file_exists.side_effect = Exception("Error de conexión a S3")
        
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    def test_download_unauthorized_access(self):
        """
        Prueba el acceso no autorizado a documentos.
        
        Casos cubiertos:
        - Usuario de otra empresa
        - Documento inexistente
        - Sin autenticación
        """
        # Crear usuario de otra empresa
        other_company = Company.objects.create(
            name="Otra Empresa",
            legal_name="Otra Empresa S.A.S.",
            tax_id="900123456-5",
            email="otra2@empresa.com"
        )
        
        other_user = User.objects.create_user(
            username="other_user2",
            email="other2@test.com",
            password="testpass123",
            company=other_company
        )
        
        # Autenticar como usuario de otra empresa
        token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        # Intentar descargar documento de otra empresa
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Probar sin autenticación
        self.client.credentials()
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentManagementTestCase(APITestCase):
    """
    Casos de prueba para la gestión completa de documentos.
    
    Cubre:
    - Listado de documentos
    - Filtros y búsquedas
    - Estadísticas
    - Eliminación
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de gestión."""
        self.company = Company.objects.create(
            name="Empresa Test Management",
            legal_name="Empresa Test Management S.A.S.",
            tax_id="900123456-6",
            email="management@test.com"
        )
        
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id="VEH004",
            name="Vehículo Test Management"
        )
        
        self.user = User.objects.create_user(
            username="management_user",
            email="management@test.com",
            password="testpass123",
            company=self.company
        )
        
        # Crear múltiples documentos con diferentes estados
        self.documents = []
        
        # Documento sin validación
        doc1 = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="doc1.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/doc1.pdf",
            created_by=self.user
        )
        self.documents.append(doc1)
        
        # Documento pendiente
        doc2 = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="doc2.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            bucket_key="test/doc2.pdf",
            created_by=self.user,
            validation_status='P'
        )
        
        # Crear flujo de validación para doc2
        validation_flow = ValidationFlow.objects.create(document=doc2)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.user
        )
        self.documents.append(doc2)
        
        # Documento aprobado
        doc3 = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="doc3.pdf",
            mime_type="application/pdf",
            size_bytes=3072,
            bucket_key="test/doc3.pdf",
            created_by=self.user,
            validation_status='A'
        )
        self.documents.append(doc3)
        
        # Documento rechazado
        doc4 = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="doc4.pdf",
            mime_type="application/pdf",
            size_bytes=4096,
            bucket_key="test/doc4.pdf",
            created_by=self.user,
            validation_status='R'
        )
        self.documents.append(doc4)
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def test_list_documents(self):
        """
        Prueba el listado de documentos.
        
        Casos cubiertos:
        - Listado completo
        - Paginación
        - Ordenamiento
        """
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 4)
        
        # Verificar que se incluyen todos los documentos
        document_names = [doc['name'] for doc in response.data['results']]
        self.assertIn('doc1.pdf', document_names)
        self.assertIn('doc2.pdf', document_names)
        self.assertIn('doc3.pdf', document_names)
        self.assertIn('doc4.pdf', document_names)
    
    def test_get_document_details(self):
        """
        Prueba la obtención de detalles de un documento.
        
        Casos cubiertos:
        - Información completa
        - Metadatos
        - Estados de validación
        """
        response = self.client.get(f'/api/documents/{self.documents[0].id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'doc1.pdf')
        self.assertEqual(response.data['mime_type'], 'application/pdf')
        self.assertEqual(response.data['size_bytes'], 1024)
        self.assertIn('company', response.data)
        self.assertIn('entity', response.data)
        self.assertIn('created_by', response.data)
    
    def test_get_validation_status(self):
        """
        Prueba la obtención del estado de validación.
        
        Casos cubiertos:
        - Documento con validación
        - Documento sin validación
        - Información de pasos
        """
        # Documento con validación
        response = self.client.get(f'/api/documents/{self.documents[1].id}/validation_status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_validation'])
        self.assertEqual(response.data['status'], 'P')
        self.assertTrue(response.data['is_active'])
        self.assertFalse(response.data['is_completed'])
        self.assertFalse(response.data['is_rejected'])
        self.assertEqual(len(response.data['steps']), 1)
        
        # Documento sin validación
        response = self.client.get(f'/api/documents/{self.documents[0].id}/validation_status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_validation'])
        self.assertIsNone(response.data['status'])
        self.assertEqual(len(response.data['steps']), 0)
    
    def test_get_pending_approvals(self):
        """
        Prueba la obtención de documentos pendientes de aprobación.
        
        Casos cubiertos:
        - Filtrado por estado
        - Usuario aprobador
        """
        response = self.client.get('/api/documents/pending_approvals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Solo doc2 está pendiente
        self.assertEqual(response.data[0]['name'], 'doc2.pdf')
    
    def test_get_approval_stats(self):
        """
        Prueba la obtención de estadísticas de aprobación.
        
        Casos cubiertos:
        - Contadores correctos
        - Estadísticas por usuario
        """
        response = self.client.get('/api/documents/approval_stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approved', response.data)
        self.assertIn('rejected', response.data)
        self.assertIn('pending', response.data)
        self.assertIn('total_actions', response.data)
    
    @patch('documents.services.storage_service')
    def test_delete_document(self, mock_storage):
        """
        Prueba la eliminación de documentos.
        
        Casos cubiertos:
        - Eliminación exitosa
        - Eliminación del archivo en bucket
        - Eliminación del registro en BD
        """
        # Mock de eliminación exitosa
        mock_storage.delete_file.return_value = True
        
        document_id = self.documents[0].id
        response = self.client.delete(f'/api/documents/{document_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que el documento fue eliminado
        self.assertFalse(Document.objects.filter(id=document_id).exists())
        
        # Verificar que se llamó la eliminación del archivo
        mock_storage.delete_file.assert_called_once_with(self.documents[0].bucket_key)


class ErrorHandlingTestCase(APITestCase):
    """
    Casos de prueba para el manejo de errores.
    
    Cubre:
    - Errores de validación
    - Errores de permisos
    - Errores de sistema
    - Mensajes de error apropiados
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de manejo de errores."""
        self.company = Company.objects.create(
            name="Empresa Test Errors",
            legal_name="Empresa Test Errors S.A.S.",
            tax_id="900123456-7",
            email="errors@test.com"
        )
        
        self.user = User.objects.create_user(
            username="error_user",
            email="error@test.com",
            password="testpass123",
            company=self.company
        )
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def test_invalid_json_format(self):
        """
        Prueba el manejo de JSON inválido.
        """
        response = self.client.post(
            '/api/documents/',
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_required_fields(self):
        """
        Prueba el manejo de campos requeridos faltantes.
        """
        incomplete_data = {
            "company_id": str(self.company.id),
            # Faltan campos requeridos
        }
        
        response = self.client.post('/api/documents/', incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_invalid_uuid_format(self):
        """
        Prueba el manejo de UUIDs inválidos.
        """
        invalid_data = {
            "company_id": "invalid-uuid",
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "test.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
                "bucket_key": "test/test.pdf"
            }
        }
        
        response = self.client.post('/api/documents/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_nonexistent_resource(self):
        """
        Prueba el manejo de recursos inexistentes.
        """
        fake_id = str(uuid.uuid4())
        
        response = self.client.get(f'/api/documents/{fake_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthorized_access(self):
        """
        Prueba el acceso no autorizado.
        """
        # Sin autenticación
        self.client.credentials()
        
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_method_not_allowed(self):
        """
        Prueba métodos HTTP no permitidos.
        """
        response = self.client.patch('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
