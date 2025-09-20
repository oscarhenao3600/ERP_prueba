"""
Pruebas unitarias para los servicios del sistema ERP de gestión de documentos.

Este módulo contiene las pruebas para los servicios de cloud storage
y validación jerárquica.
"""

import uuid
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError

from companies.models import Company, Entity, EntityType, User
from documents.models import Document, ValidationFlow, ValidationStep, ValidationAction
from documents.services import S3StorageService, GCSStorageService, CloudStorageService
from documents.validation_service import ValidationService


class CloudStorageServiceTest(TestCase):
    """Pruebas para el servicio base de cloud storage."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.service = CloudStorageService()
    
    def test_generate_bucket_key(self):
        """Prueba la generación de claves de bucket."""
        company_id = str(uuid.uuid4())
        entity_type = "vehicle"
        entity_id = "VEH001"
        filename = "test.pdf"
        
        bucket_key = self.service.generate_bucket_key(
            company_id, entity_type, entity_id, filename
        )
        
        self.assertTrue(bucket_key.startswith(f"companies/{company_id}/{entity_type}/{entity_id}/docs/"))
        self.assertTrue(bucket_key.endswith(".pdf"))
        self.assertIn(str(uuid.UUID(company_id)), bucket_key)
    
    def test_validate_file_valid(self):
        """Prueba la validación de archivos válidos."""
        file_data = b"test content"
        mime_type = "application/pdf"
        size_bytes = 1024
        
        # No debe lanzar excepción
        self.service.validate_file(file_data, mime_type, size_bytes)
    
    def test_validate_file_too_large(self):
        """Prueba la validación de archivos demasiado grandes."""
        file_data = b"test content"
        mime_type = "application/pdf"
        size_bytes = 20000000  # 20MB
        
        with self.assertRaises(ValidationError):
            self.service.validate_file(file_data, mime_type, size_bytes)
    
    def test_validate_file_invalid_mime(self):
        """Prueba la validación de tipos MIME inválidos."""
        file_data = b"test content"
        mime_type = "application/invalid"
        size_bytes = 1024
        
        with self.assertRaises(ValidationError):
            self.service.validate_file(file_data, mime_type, size_bytes)
    
    def test_validate_file_empty(self):
        """Prueba la validación de archivos vacíos."""
        file_data = b""
        mime_type = "application/pdf"
        size_bytes = 0
        
        with self.assertRaises(ValidationError):
            self.service.validate_file(file_data, mime_type, size_bytes)
    
    def test_calculate_file_hash(self):
        """Prueba el cálculo de hash de archivos."""
        file_data = b"test content"
        hash_result = self.service.calculate_file_hash(file_data)
        
        self.assertEqual(len(hash_result), 64)  # SHA-256 produce hash de 64 caracteres
        self.assertIsInstance(hash_result, str)


class S3StorageServiceTest(TestCase):
    """Pruebas para el servicio de S3."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        with patch('documents.services.boto3.client'):
            self.service = S3StorageService()
            self.service.s3_client = Mock()
    
    def test_generate_presigned_upload_url(self):
        """Prueba la generación de URLs pre-firmadas para subida."""
        bucket_key = "test/test.pdf"
        mime_type = "application/pdf"
        
        # Mock de la respuesta de S3
        mock_response = {
            'url': 'https://test-bucket.s3.amazonaws.com/',
            'fields': {'Content-Type': mime_type}
        }
        self.service.s3_client.generate_presigned_post.return_value = mock_response
        
        result = self.service.generate_presigned_upload_url(bucket_key, mime_type)
        
        self.assertEqual(result['url'], mock_response['url'])
        self.assertEqual(result['fields'], mock_response['fields'])
        self.service.s3_client.generate_presigned_post.assert_called_once()
    
    def test_generate_presigned_download_url(self):
        """Prueba la generación de URLs pre-firmadas para descarga."""
        bucket_key = "test/test.pdf"
        mock_url = "https://test-bucket.s3.amazonaws.com/test/test.pdf"
        
        self.service.s3_client.generate_presigned_url.return_value = mock_url
        
        result = self.service.generate_presigned_download_url(bucket_key)
        
        self.assertEqual(result, mock_url)
        self.service.s3_client.generate_presigned_url.assert_called_once()
    
    def test_file_exists_true(self):
        """Prueba la verificación de existencia de archivos (existe)."""
        bucket_key = "test/test.pdf"
        
        self.service.s3_client.head_object.return_value = {}
        
        result = self.service.file_exists(bucket_key)
        
        self.assertTrue(result)
        self.service.s3_client.head_object.assert_called_once()
    
    def test_file_exists_false(self):
        """Prueba la verificación de existencia de archivos (no existe)."""
        bucket_key = "test/test.pdf"
        
        from botocore.exceptions import ClientError
        self.service.s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404'}}, 'HeadObject'
        )
        
        result = self.service.file_exists(bucket_key)
        
        self.assertFalse(result)
    
    def test_delete_file(self):
        """Prueba la eliminación de archivos."""
        bucket_key = "test/test.pdf"
        
        result = self.service.delete_file(bucket_key)
        
        self.assertTrue(result)
        self.service.s3_client.delete_object.assert_called_once()
    
    def test_get_file_metadata(self):
        """Prueba la obtención de metadatos de archivos."""
        bucket_key = "test/test.pdf"
        mock_metadata = {
            'ContentLength': 1024,
            'ContentType': 'application/pdf',
            'LastModified': '2023-01-01T00:00:00Z',
            'ETag': '"test-etag"'
        }
        
        self.service.s3_client.head_object.return_value = mock_metadata
        
        result = self.service.get_file_metadata(bucket_key)
        
        self.assertEqual(result['size'], 1024)
        self.assertEqual(result['mime_type'], 'application/pdf')
        self.service.s3_client.head_object.assert_called_once()


class ValidationServiceTest(TestCase):
    """Pruebas para el servicio de validación jerárquica."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.company = Company.objects.create(
            name="Empresa Test",
            legal_name="Empresa Test S.A.S.",
            tax_id="900123456-1",
            email="test@empresa.com"
        )
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id="VEH001",
            name="Vehículo Test"
        )
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="testpass123",
            company=self.company
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="testpass123",
            company=self.company
        )
        self.user3 = User.objects.create_user(
            username="user3",
            email="user3@test.com",
            password="testpass123",
            company=self.company
        )
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user1
        )
    
    def test_create_validation_flow(self):
        """Prueba la creación de un flujo de validación."""
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)},
            {'order': 3, 'approver_user_id': str(self.user3.id)}
        ]
        
        validation_flow = ValidationService.create_validation_flow(self.document, steps_data)
        
        self.assertEqual(validation_flow.document, self.document)
        self.assertTrue(validation_flow.is_active)
        self.assertEqual(self.document.validation_status, 'P')
        
        # Verificar que se crearon los pasos
        steps = validation_flow.get_steps()
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].order, 1)
        self.assertEqual(steps[0].approver, self.user1)
        self.assertEqual(steps[1].order, 2)
        self.assertEqual(steps[1].approver, self.user2)
        self.assertEqual(steps[2].order, 3)
        self.assertEqual(steps[2].approver, self.user3)
    
    def test_create_validation_flow_empty_steps(self):
        """Prueba la creación de un flujo sin pasos."""
        with self.assertRaises(ValidationError):
            ValidationService.create_validation_flow(self.document, [])
    
    def test_create_validation_flow_duplicate_orders(self):
        """Prueba la creación de un flujo con órdenes duplicados."""
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 1, 'approver_user_id': str(self.user2.id)}  # Orden duplicado
        ]
        
        with self.assertRaises(ValidationError):
            ValidationService.create_validation_flow(self.document, steps_data)
    
    def test_create_validation_flow_wrong_company(self):
        """Prueba la creación de un flujo con aprobador de otra empresa."""
        other_company = Company.objects.create(
            name="Otra Empresa",
            legal_name="Otra Empresa S.A.S.",
            tax_id="900123456-2",
            email="otra@empresa.com"
        )
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@test.com",
            password="testpass123",
            company=other_company
        )
        
        steps_data = [
            {'order': 1, 'approver_user_id': str(other_user.id)}
        ]
        
        with self.assertRaises(ValidationError):
            ValidationService.create_validation_flow(self.document, steps_data)
    
    def test_approve_document_hierarchy(self):
        """Prueba la aprobación con regla de jerarquía."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)},
            {'order': 3, 'approver_user_id': str(self.user3.id)}
        ]
        validation_flow = ValidationService.create_validation_flow(self.document, steps_data)
        
        # Aprobar con usuario de mayor jerarquía (orden 3)
        action = ValidationService.approve_document(self.document, self.user3, "Aprobado")
        
        self.assertEqual(action.action, 'A')
        self.assertEqual(action.actor, self.user3)
        
        # Verificar que se aprobaron automáticamente los pasos previos
        steps = validation_flow.get_steps()
        self.assertEqual(steps[0].status, 'A')  # Paso 1 aprobado automáticamente
        self.assertEqual(steps[1].status, 'A')  # Paso 2 aprobado automáticamente
        self.assertEqual(steps[2].status, 'A')  # Paso 3 aprobado por el usuario
        
        # Verificar que el documento está aprobado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'A')
    
    def test_approve_document_intermediate_step(self):
        """Prueba la aprobación de un paso intermedio."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)},
            {'order': 3, 'approver_user_id': str(self.user3.id)}
        ]
        validation_flow = ValidationService.create_validation_flow(self.document, steps_data)
        
        # Aprobar con usuario de orden intermedio (orden 2)
        action = ValidationService.approve_document(self.document, self.user2, "Aprobado")
        
        self.assertEqual(action.action, 'A')
        self.assertEqual(action.actor, self.user2)
        
        # Verificar que se aprobó automáticamente el paso previo
        steps = validation_flow.get_steps()
        self.assertEqual(steps[0].status, 'A')  # Paso 1 aprobado automáticamente
        self.assertEqual(steps[1].status, 'A')  # Paso 2 aprobado por el usuario
        self.assertEqual(steps[2].status, 'P')  # Paso 3 sigue pendiente
        
        # Verificar que el documento sigue pendiente
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'P')
    
    def test_reject_document(self):
        """Prueba el rechazo de un documento."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        validation_flow = ValidationService.create_validation_flow(self.document, steps_data)
        
        # Rechazar con cualquier usuario
        action = ValidationService.reject_document(self.document, self.user1, "Rechazado")
        
        self.assertEqual(action.action, 'R')
        self.assertEqual(action.actor, self.user1)
        
        # Verificar que el paso fue rechazado
        step = validation_flow.steps.get(order=1)
        self.assertEqual(step.status, 'R')
        
        # Verificar que el documento está rechazado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'R')
        
        # Verificar que el flujo está desactivado
        validation_flow.refresh_from_db()
        self.assertFalse(validation_flow.is_active)
    
    def test_approve_document_no_permission(self):
        """Prueba la aprobación sin permisos."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)}
        ]
        ValidationService.create_validation_flow(self.document, steps_data)
        
        # Intentar aprobar con usuario que no es aprobador
        with self.assertRaises(ValidationError):
            ValidationService.approve_document(self.document, self.user2, "Aprobado")
    
    def test_reject_document_no_permission(self):
        """Prueba el rechazo sin permisos."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)}
        ]
        ValidationService.create_validation_flow(self.document, steps_data)
        
        # Intentar rechazar con usuario que no es aprobador
        with self.assertRaises(ValidationError):
            ValidationService.reject_document(self.document, self.user2, "Rechazado")
    
    def test_get_validation_status(self):
        """Prueba la obtención del estado de validación."""
        # Sin flujo de validación
        status = ValidationService.get_validation_status(self.document)
        self.assertFalse(status['has_validation'])
        self.assertIsNone(status['status'])
        
        # Con flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        validation_flow = ValidationService.create_validation_flow(self.document, steps_data)
        
        status = ValidationService.get_validation_status(self.document)
        self.assertTrue(status['has_validation'])
        self.assertEqual(status['status'], 'P')
        self.assertTrue(status['is_active'])
        self.assertFalse(status['is_completed'])
        self.assertFalse(status['is_rejected'])
        self.assertEqual(len(status['steps']), 2)
    
    def test_get_pending_approvals_for_user(self):
        """Prueba la obtención de documentos pendientes para un usuario."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        ValidationService.create_validation_flow(self.document, steps_data)
        
        # Obtener documentos pendientes para user1
        pending = ValidationService.get_pending_approvals_for_user(self.user1)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0], self.document)
        
        # Obtener documentos pendientes para user2
        pending = ValidationService.get_pending_approvals_for_user(self.user2)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0], self.document)
        
        # Obtener documentos pendientes para user3 (no es aprobador)
        pending = ValidationService.get_pending_approvals_for_user(self.user3)
        self.assertEqual(len(pending), 0)
    
    def test_get_user_approval_stats(self):
        """Prueba la obtención de estadísticas de aprobación de un usuario."""
        # Crear flujo de validación
        steps_data = [
            {'order': 1, 'approver_user_id': str(self.user1.id)}
        ]
        ValidationService.create_validation_flow(self.document, steps_data)
        
        # Aprobar documento
        ValidationService.approve_document(self.document, self.user1, "Aprobado")
        
        # Obtener estadísticas
        stats = ValidationService.get_user_approval_stats(self.user1)
        self.assertEqual(stats['approved'], 1)
        self.assertEqual(stats['rejected'], 0)
        self.assertEqual(stats['total_actions'], 1)
        
        # Crear otro documento y rechazarlo
        document2 = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test2.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test2.pdf",
            created_by=self.user1
        )
        steps_data2 = [
            {'order': 1, 'approver_user_id': str(self.user1.id)}
        ]
        ValidationService.create_validation_flow(document2, steps_data2)
        ValidationService.reject_document(document2, self.user1, "Rechazado")
        
        # Obtener estadísticas actualizadas
        stats = ValidationService.get_user_approval_stats(self.user1)
        self.assertEqual(stats['approved'], 1)
        self.assertEqual(stats['rejected'], 1)
        self.assertEqual(stats['total_actions'], 2)
