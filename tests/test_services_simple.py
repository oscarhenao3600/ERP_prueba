"""
Pruebas simplificadas para los servicios del sistema ERP de gestión de documentos.

Este módulo contiene pruebas básicas para los servicios principales,
usando el servicio mock para evitar dependencias externas.
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.exceptions import ValidationError

from companies.models import Company, Entity, EntityType, User
from documents.models import Document, ValidationFlow, ValidationStep, ValidationAction
from documents.services_test import MockCloudStorageService
from documents.validation_service import ValidationService


class MockCloudStorageServiceTest(TestCase):
    """Pruebas para el servicio mock de cloud storage."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.service = MockCloudStorageService()
        
        # Crear datos de prueba
        self.company = Company.objects.create(
            name='Empresa Test',
            legal_name='Empresa Test S.A.S.',
            tax_id='900123456-1',
            email='test@empresa.com',
            phone='+57-1-234-5678',
            address='Calle 123 #45-67'
        )
        
        self.entity_type = EntityType.objects.create(
            name='vehicle',
            display_name='Vehículo',
            description='Vehículos de la empresa',
            is_active=True
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id='VEH001',
            name='Vehículo Test',
            metadata='{"modelo": "Toyota Corolla"}',
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            company=self.company,
            employee_id='EMP001',
            phone='+57-1-234-5679',
            position='Desarrollador',
            department='Tecnología'
        )

    def test_service_initialization(self):
        """Prueba la inicialización del servicio mock."""
        self.assertIsNotNone(self.service.bucket_name)
        self.assertIsNotNone(self.service.url_expiration)
        self.assertIsNotNone(self.service.max_file_size)
        self.assertIsNotNone(self.service.allowed_mime_types)
        self.assertIsInstance(self.service._storage, dict)

    def test_validate_file_valid(self):
        """Prueba la validación de archivos válidos."""
        # Archivo válido
        self.service.validate_file('application/pdf', 1024)
        self.service.validate_file('image/jpeg', 2048)
        self.service.validate_file('image/png', 512)

    def test_validate_file_invalid_mime_type(self):
        """Prueba la validación con tipo MIME inválido."""
        with self.assertRaises(ValidationError):
            self.service.validate_file('application/x-executable', 1024)

    def test_validate_file_too_large(self):
        """Prueba la validación con archivo demasiado grande."""
        with self.assertRaises(ValidationError):
            self.service.validate_file('application/pdf', 20000000)  # 20MB

    def test_validate_file_zero_size(self):
        """Prueba la validación con tamaño cero."""
        with self.assertRaises(ValidationError):
            self.service.validate_file('application/pdf', 0)

    def test_generate_bucket_key(self):
        """Prueba la generación de claves de bucket."""
        key = self.service.generate_bucket_key(
            str(self.company.id),
            'vehicle',
            'VEH001',
            'test.pdf'
        )
        
        self.assertIn('companies', key)
        self.assertIn(str(self.company.id), key)
        self.assertIn('vehicle', key)
        self.assertIn('VEH001', key)
        self.assertIn('test.pdf', key)

    def test_generate_presigned_upload_url(self):
        """Prueba la generación de URL de subida."""
        result = self.service.generate_presigned_upload_url(
            'test/file.pdf',
            'application/pdf'
        )
        
        self.assertIn('url', result)
        self.assertIn('fields', result)
        self.assertEqual(result['fields']['Content-Type'], 'application/pdf')
        self.assertIn('upload', result['url'])

    def test_generate_presigned_download_url_file_exists(self):
        """Prueba la generación de URL de descarga para archivo existente."""
        # Simular archivo existente
        self.service._storage['test/file.pdf'] = {
            'size': 1024,
            'mime_type': 'application/pdf'
        }
        
        result = self.service.generate_presigned_download_url('test/file.pdf')
        
        self.assertIn('download', result)
        self.assertIn('test/file.pdf', result)

    def test_generate_presigned_download_url_file_not_exists(self):
        """Prueba la generación de URL de descarga para archivo inexistente."""
        with self.assertRaises(ValidationError):
            self.service.generate_presigned_download_url('nonexistent/file.pdf')

    def test_file_exists_true(self):
        """Prueba la verificación de existencia de archivo (existe)."""
        self.service._storage['test/file.pdf'] = {'size': 1024}
        
        result = self.service.file_exists('test/file.pdf')
        self.assertTrue(result)

    def test_file_exists_false(self):
        """Prueba la verificación de existencia de archivo (no existe)."""
        result = self.service.file_exists('nonexistent/file.pdf')
        self.assertFalse(result)

    def test_delete_file_exists(self):
        """Prueba la eliminación de archivo existente."""
        self.service._storage['test/file.pdf'] = {'size': 1024}
        
        result = self.service.delete_file('test/file.pdf')
        self.assertTrue(result)
        self.assertNotIn('test/file.pdf', self.service._storage)

    def test_delete_file_not_exists(self):
        """Prueba la eliminación de archivo inexistente."""
        result = self.service.delete_file('nonexistent/file.pdf')
        self.assertFalse(result)

    def test_get_file_metadata_exists(self):
        """Prueba la obtención de metadatos de archivo existente."""
        metadata = {'size': 1024, 'mime_type': 'application/pdf'}
        self.service._storage['test/file.pdf'] = metadata
        
        result = self.service.get_file_metadata('test/file.pdf')
        self.assertEqual(result, metadata)

    def test_get_file_metadata_not_exists(self):
        """Prueba la obtención de metadatos de archivo inexistente."""
        result = self.service.get_file_metadata('nonexistent/file.pdf')
        self.assertIsNone(result)

    def test_store_file(self):
        """Prueba el almacenamiento de metadatos de archivo."""
        metadata = {'size': 1024, 'mime_type': 'application/pdf'}
        
        result = self.service.store_file('test/file.pdf', metadata)
        self.assertTrue(result)
        self.assertEqual(self.service._storage['test/file.pdf'], metadata)


class ValidationServiceTest(TestCase):
    """Pruebas para el servicio de validación jerárquica."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.company = Company.objects.create(
            name='Empresa Test',
            legal_name='Empresa Test S.A.S.',
            tax_id='900123456-2',
            email='test2@empresa.com',
            phone='+57-1-234-5678',
            address='Calle 123 #45-67'
        )
        
        self.entity_type = EntityType.objects.create(
            name='vehicle',
            display_name='Vehículo',
            description='Vehículos de la empresa',
            is_active=True
        )
        
        self.entity = Entity.objects.create(
            company=self.company,
            entity_type=self.entity_type,
            external_id='VEH002',
            name='Vehículo Test',
            metadata='{"modelo": "Toyota Corolla"}',
            is_active=True
        )
        
        self.user1 = User.objects.create_user(
            username='approver1',
            email='approver1@test.com',
            password='testpass123',
            company=self.company,
            employee_id='EMP001',
            phone='+57-1-234-5679',
            position='Aprobador',
            department='Recursos Humanos'
        )
        
        self.user2 = User.objects.create_user(
            username='approver2',
            email='approver2@test.com',
            password='testpass123',
            company=self.company,
            employee_id='EMP002',
            phone='+57-1-234-5680',
            position='Gerente',
            department='Administración'
        )
        
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name='test_document.pdf',
            mime_type='application/pdf',
            size_bytes=1024,
            bucket_key='test/test_document.pdf',
            file_hash='test_hash',
            description='Documento de prueba',
            tags='["test", "documento"]',
            created_by=self.user1
        )

    def test_create_validation_flow(self):
        """Prueba la creación de un flujo de validación."""
        approvers = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        
        validation_flow = ValidationService.create_validation_flow(
            self.document, approvers
        )
        
        self.assertIsNotNone(validation_flow)
        self.assertEqual(validation_flow.document, self.document)
        self.assertTrue(validation_flow.is_active)
        self.assertEqual(validation_flow.steps.count(), 2)
        
        # Verificar pasos
        step1 = validation_flow.steps.get(order=1)
        step2 = validation_flow.steps.get(order=2)
        
        self.assertEqual(step1.approver, self.user1)
        self.assertEqual(step2.approver, self.user2)
        self.assertEqual(step1.status, 'P')
        self.assertEqual(step2.status, 'P')

    def test_approve_document_step(self):
        """Prueba la aprobación de un paso de validación."""
        # Crear flujo de validación
        approvers = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        
        validation_flow = ValidationService.create_validation_flow(
            self.document, approvers
        )
        
        # Aprobar paso 2 (mayor jerarquía)
        result = ValidationService.approve_document(
            self.document, self.user2, "Documento aprobado por gerencia"
        )
        
        self.assertTrue(result)
        
        # Verificar que ambos pasos fueron aprobados
        step1 = validation_flow.steps.get(order=1)
        step2 = validation_flow.steps.get(order=2)
        
        self.assertEqual(step1.status, 'A')
        self.assertEqual(step2.status, 'A')
        
        # Verificar que el documento está aprobado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'A')
        
        # Verificar que se creó la acción de validación
        action = ValidationAction.objects.filter(
            document=self.document,
            actor=self.user2
        ).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.action, 'A')
        self.assertEqual(action.reason, "Documento aprobado por gerencia")

    def test_reject_document(self):
        """Prueba el rechazo de un documento."""
        # Crear flujo de validación
        approvers = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        
        validation_flow = ValidationService.create_validation_flow(
            self.document, approvers
        )
        
        # Rechazar documento
        result = ValidationService.reject_document(
            self.document, self.user1, "Documento no cumple requisitos"
        )
        
        self.assertTrue(result)
        
        # Verificar que el documento está rechazado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'R')
        
        # Verificar que el flujo está desactivado
        validation_flow.refresh_from_db()
        self.assertFalse(validation_flow.is_active)
        
        # Verificar que se creó la acción de rechazo
        action = ValidationAction.objects.filter(
            document=self.document,
            actor=self.user1
        ).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.action, 'R')
        self.assertEqual(action.reason, "Documento no cumple requisitos")

    def test_approve_document_invalid_user(self):
        """Prueba la aprobación con usuario no autorizado."""
        # Crear flujo de validación
        approvers = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        
        ValidationService.create_validation_flow(self.document, approvers)
        
        # Intentar aprobar con usuario no autorizado
        with self.assertRaises(ValidationError):
            ValidationService.approve_document(
                self.document, 
                User.objects.create_user(
                    username='unauthorized',
                    email='unauthorized@test.com',
                    password='testpass123',
                    company=self.company,
                    employee_id='EMP003',
                    phone='+57-1-234-5681',
                    position='Empleado',
                    department='Ventas'
                ),
                "Intento no autorizado"
            )

    def test_approve_document_already_rejected(self):
        """Prueba la aprobación de un documento ya rechazado."""
        # Crear flujo de validación
        approvers = [
            {'order': 1, 'approver_user_id': str(self.user1.id)},
            {'order': 2, 'approver_user_id': str(self.user2.id)}
        ]
        
        ValidationService.create_validation_flow(self.document, approvers)
        
        # Rechazar documento
        ValidationService.reject_document(
            self.document, self.user1, "Documento rechazado"
        )
        
        # Intentar aprobar documento rechazado
        with self.assertRaises(ValidationError):
            ValidationService.approve_document(
                self.document, self.user2, "Intento de aprobación después del rechazo"
            )
