"""
Pruebas unitarias para las vistas y API del sistema ERP de gestión de documentos.

Este módulo contiene las pruebas para las vistas de Django REST Framework
y los endpoints de la API.
"""

import json
import uuid
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from companies.models import Company, Entity, EntityType, User
from documents.models import Document, ValidationFlow, ValidationStep, ValidationAction

User = get_user_model()


class DocumentAPITest(APITestCase):
    """Pruebas para la API de documentos."""
    
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
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.approver = User.objects.create_user(
            username="approver",
            email="approver@test.com",
            password="testpass123",
            company=self.company,
            is_company_admin=True
        )
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user
        )
    
    def test_create_document_without_validation(self):
        """Prueba la creación de un documento sin flujo de validación."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "nuevo.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 2048,
                "bucket_key": "test/nuevo.pdf",
                "description": "Documento de prueba"
            }
        }
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 2)
        
        new_document = Document.objects.get(name="nuevo.pdf")
        self.assertEqual(new_document.company, self.company)
        self.assertEqual(new_document.entity, self.entity)
        self.assertEqual(new_document.description, "Documento de prueba")
        self.assertIsNone(new_document.validation_status)
    
    def test_create_document_with_validation(self):
        """Prueba la creación de un documento con flujo de validación."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "validacion.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 2048,
                "bucket_key": "test/validacion.pdf"
            },
            "validation_flow": {
                "enabled": True,
                "steps": [
                    {"order": 1, "approver_user_id": str(self.approver.id)}
                ]
            }
        }
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_document = Document.objects.get(name="validacion.pdf")
        self.assertEqual(new_document.validation_status, 'P')
        
        # Verificar que se creó el flujo de validación
        validation_flow = new_document.validation_flow
        self.assertTrue(validation_flow.is_active)
        self.assertEqual(validation_flow.steps.count(), 1)
        self.assertEqual(validation_flow.steps.first().approver, self.approver)
    
    def test_create_document_invalid_company(self):
        """Prueba la creación de un documento con empresa inválida."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(uuid.uuid4()),  # ID inexistente
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
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_create_document_invalid_entity(self):
        """Prueba la creación de un documento con entidad inválida."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "invalid_type",
                "entity_id": "INV001"
            },
            "document": {
                "name": "test.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
                "bucket_key": "test/test.pdf"
            }
        }
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_create_document_invalid_mime_type(self):
        """Prueba la creación de un documento con tipo MIME inválido."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "test.txt",
                "mime_type": "text/plain",  # Tipo no permitido
                "size_bytes": 1024,
                "bucket_key": "test/test.txt"
            }
        }
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_create_document_too_large(self):
        """Prueba la creación de un documento demasiado grande."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "company_id": str(self.company.id),
            "entity": {
                "entity_type": "vehicle",
                "entity_id": "VEH001"
            },
            "document": {
                "name": "large.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 20000000,  # 20MB
                "bucket_key": "test/large.pdf"
            }
        }
        
        response = self.client.post('/api/documents/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('documents.services.storage_service')
    def test_upload_url_generation(self, mock_storage):
        """Prueba la generación de URLs pre-firmadas para subida."""
        self.client.force_authenticate(user=self.user)
        
        # Mock de la respuesta del servicio de storage
        mock_storage.generate_presigned_upload_url.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/',
            'fields': {'Content-Type': 'application/pdf'}
        }
        
        data = {
            "company_id": str(self.company.id),
            "entity_type": "vehicle",
            "entity_id": "VEH001",
            "filename": "test.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024
        }
        
        response = self.client.post('/api/documents/upload_url/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('upload_url', response.data)
        self.assertIn('bucket_key', response.data)
        self.assertIn('fields', response.data)
    
    @patch('documents.services.storage_service')
    def test_download_url_generation(self, mock_storage):
        """Prueba la generación de URLs pre-firmadas para descarga."""
        self.client.force_authenticate(user=self.user)
        
        # Mock de la respuesta del servicio de storage
        mock_storage.file_exists.return_value = True
        mock_storage.generate_presigned_download_url.return_value = 'https://test-bucket.s3.amazonaws.com/test/test.pdf'
        
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        self.assertEqual(response.data['filename'], 'test.pdf')
        self.assertEqual(response.data['mime_type'], 'application/pdf')
    
    @patch('documents.services.storage_service')
    def test_download_file_not_found(self, mock_storage):
        """Prueba la descarga de un archivo que no existe en el bucket."""
        self.client.force_authenticate(user=self.user)
        
        # Mock de archivo no encontrado
        mock_storage.file_exists.return_value = False
        
        response = self.client.get(f'/api/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_approve_document(self):
        """Prueba la aprobación de un documento."""
        # Crear flujo de validación
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        self.client.force_authenticate(user=self.approver)
        
        data = {
            "actor_user_id": str(self.approver.id),
            "reason": "Documento aprobado"
        }
        
        response = self.client.post(f'/api/documents/{self.document.id}/approve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('document', response.data)
        
        # Verificar que el documento fue aprobado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'A')
        
        # Verificar que se creó la acción de validación
        action = ValidationAction.objects.filter(document=self.document).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.action, 'A')
        self.assertEqual(action.actor, self.approver)
    
    def test_reject_document(self):
        """Prueba el rechazo de un documento."""
        # Crear flujo de validación
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        self.client.force_authenticate(user=self.approver)
        
        data = {
            "actor_user_id": str(self.approver.id),
            "reason": "Documento rechazado"
        }
        
        response = self.client.post(f'/api/documents/{self.document.id}/reject/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('document', response.data)
        
        # Verificar que el documento fue rechazado
        self.document.refresh_from_db()
        self.assertEqual(self.document.validation_status, 'R')
        
        # Verificar que el flujo fue desactivado
        validation_flow.refresh_from_db()
        self.assertFalse(validation_flow.is_active)
    
    def test_approve_document_no_permission(self):
        """Prueba la aprobación sin permisos."""
        # Crear flujo de validación
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        # Autenticar con usuario que no es aprobador
        self.client.force_authenticate(user=self.user)
        
        data = {
            "actor_user_id": str(self.user.id),
            "reason": "Intento de aprobación"
        }
        
        response = self.client.post(f'/api/documents/{self.document.id}/approve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_validation_status(self):
        """Prueba la obtención del estado de validación."""
        # Crear flujo de validación
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/documents/{self.document.id}/validation_status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_validation'])
        self.assertEqual(response.data['status'], 'P')
        self.assertTrue(response.data['is_active'])
        self.assertEqual(len(response.data['steps']), 1)
    
    def test_get_pending_approvals(self):
        """Prueba la obtención de documentos pendientes de aprobación."""
        # Crear flujo de validación
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.get('/api/documents/pending_approvals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.document.id))
    
    def test_get_approval_stats(self):
        """Prueba la obtención de estadísticas de aprobación."""
        # Crear flujo de validación y aprobar documento
        validation_flow = ValidationFlow.objects.create(document=self.document)
        ValidationStep.objects.create(
            validation_flow=validation_flow,
            order=1,
            approver=self.approver
        )
        self.document.validation_status = 'P'
        self.document.save()
        
        ValidationAction.objects.create(
            document=self.document,
            validation_step=validation_flow.steps.first(),
            actor=self.approver,
            action='A',
            reason="Aprobado"
        )
        
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.get('/api/documents/approval_stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approved', response.data)
        self.assertIn('rejected', response.data)
        self.assertIn('pending', response.data)
        self.assertIn('total_actions', response.data)
    
    def test_list_documents(self):
        """Prueba la listación de documentos."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.document.id))
    
    def test_retrieve_document(self):
        """Prueba la obtención de un documento específico."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/documents/{self.document.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.document.id))
        self.assertEqual(response.data['name'], 'test.pdf')
    
    @patch('documents.services.storage_service')
    def test_delete_document(self, mock_storage):
        """Prueba la eliminación de un documento."""
        self.client.force_authenticate(user=self.user)
        
        # Mock de eliminación exitosa
        mock_storage.delete_file.return_value = True
        
        response = self.client.delete(f'/api/documents/{self.document.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=self.document.id).exists())
    
    def test_unauthorized_access(self):
        """Prueba el acceso no autorizado."""
        # Sin autenticación
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Con usuario de otra empresa
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
        
        self.client.force_authenticate(user=other_user)
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # No debe ver documentos de otra empresa


class CompanyAPITest(APITestCase):
    """Pruebas para la API de empresas."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.company = Company.objects.create(
            name="Empresa Test",
            legal_name="Empresa Test S.A.S.",
            tax_id="900123456-1",
            email="test@empresa.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
    
    def test_list_companies(self):
        """Prueba la listación de empresas."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/companies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.company.id))
    
    def test_retrieve_company(self):
        """Prueba la obtención de una empresa específica."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/companies/{self.company.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.company.id))
        self.assertEqual(response.data['name'], 'Empresa Test')
    
    def test_company_stats(self):
        """Prueba la obtención de estadísticas de una empresa."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/companies/{self.company.id}/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users_count', response.data)
        self.assertIn('documents_count', response.data)
        self.assertIn('entities_count', response.data)
    
    def test_company_users(self):
        """Prueba la obtención de usuarios de una empresa."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/companies/{self.company.id}/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.user.id))
    
    def test_company_entities(self):
        """Prueba la obtención de entidades de una empresa."""
        entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo"
        )
        entity = Entity.objects.create(
            company=self.company,
            entity_type=entity_type,
            external_id="VEH001",
            name="Vehículo Test"
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/companies/{self.company.id}/entities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(entity.id))
