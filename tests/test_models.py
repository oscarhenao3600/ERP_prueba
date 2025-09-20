"""
Pruebas unitarias para los modelos del sistema ERP de gestión de documentos.

Este módulo contiene las pruebas para los modelos de empresas, entidades,
documentos y flujos de validación.
"""

import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from companies.models import Company, Entity, EntityType, User
from documents.models import Document, ValidationFlow, ValidationStep, ValidationAction

User = get_user_model()


class CompanyModelTest(TestCase):
    """Pruebas para el modelo Company."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.company = Company.objects.create(
            name="Empresa Test",
            legal_name="Empresa Test S.A.S.",
            tax_id="900123456-1",
            email="test@empresa.com"
        )
    
    def test_company_creation(self):
        """Prueba la creación de una empresa."""
        self.assertEqual(self.company.name, "Empresa Test")
        self.assertEqual(self.company.legal_name, "Empresa Test S.A.S.")
        self.assertEqual(self.company.tax_id, "900123456-1")
        self.assertTrue(self.company.is_active)
    
    def test_company_str(self):
        """Prueba la representación string de la empresa."""
        expected = "Empresa Test (900123456-1)"
        self.assertEqual(str(self.company), expected)
    
    def test_company_users_count(self):
        """Prueba el conteo de usuarios activos."""
        # Crear usuarios
        User.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="testpass123",
            company=self.company
        )
        User.objects.create_user(
            username="user2",
            email="user2@test.com",
            password="testpass123",
            company=self.company,
            is_active=False
        )
        
        self.assertEqual(self.company.get_active_users_count(), 1)
    
    def test_company_documents_count(self):
        """Prueba el conteo de documentos."""
        # Crear entidad y documento
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
        Document.objects.create(
            company=self.company,
            entity=entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=User.objects.create_user(
                username="creator",
                email="creator@test.com",
                password="testpass123",
                company=self.company
            )
        )
        
        self.assertEqual(self.company.get_documents_count(), 1)


class EntityTypeModelTest(TestCase):
    """Pruebas para el modelo EntityType."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.entity_type = EntityType.objects.create(
            name="vehicle",
            display_name="Vehículo",
            description="Tipo de entidad para vehículos"
        )
    
    def test_entity_type_creation(self):
        """Prueba la creación de un tipo de entidad."""
        self.assertEqual(self.entity_type.name, "vehicle")
        self.assertEqual(self.entity_type.display_name, "Vehículo")
        self.assertTrue(self.entity_type.is_active)
    
    def test_entity_type_str(self):
        """Prueba la representación string del tipo de entidad."""
        self.assertEqual(str(self.entity_type), "Vehículo")


class EntityModelTest(TestCase):
    """Pruebas para el modelo Entity."""
    
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
    
    def test_entity_creation(self):
        """Prueba la creación de una entidad."""
        self.assertEqual(self.entity.company, self.company)
        self.assertEqual(self.entity.entity_type, self.entity_type)
        self.assertEqual(self.entity.external_id, "VEH001")
        self.assertEqual(self.entity.name, "Vehículo Test")
        self.assertTrue(self.entity.is_active)
    
    def test_entity_str(self):
        """Prueba la representación string de la entidad."""
        expected = "Vehículo Test (Vehículo)"
        self.assertEqual(str(self.entity), expected)
    
    def test_entity_unique_constraint(self):
        """Prueba la restricción única de entidad."""
        with self.assertRaises(Exception):
            Entity.objects.create(
                company=self.company,
                entity_type=self.entity_type,
                external_id="VEH001",  # Mismo external_id
                name="Otro Vehículo"
            )
    
    def test_entity_documents_count(self):
        """Prueba el conteo de documentos de la entidad."""
        Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=User.objects.create_user(
                username="creator",
                email="creator@test.com",
                password="testpass123",
                company=self.company
            )
        )
        
        self.assertEqual(self.entity.get_documents_count(), 1)


class UserModelTest(TestCase):
    """Pruebas para el modelo User."""
    
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
            company=self.company,
            first_name="Test",
            last_name="User"
        )
    
    def test_user_creation(self):
        """Prueba la creación de un usuario."""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@test.com")
        self.assertEqual(self.user.company, self.company)
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_company_admin)
    
    def test_user_str(self):
        """Prueba la representación string del usuario."""
        expected = "Test User (Empresa Test)"
        self.assertEqual(str(self.user), expected)
    
    def test_user_full_name(self):
        """Prueba el método get_full_name."""
        self.assertEqual(self.user.get_full_name(), "Test User")
    
    def test_user_can_approve_documents(self):
        """Prueba el método can_approve_documents."""
        # Usuario normal no puede aprobar
        self.assertFalse(self.user.can_approve_documents())
        
        # Usuario administrador de empresa puede aprobar
        self.user.is_company_admin = True
        self.user.save()
        self.assertTrue(self.user.can_approve_documents())
        
        # Usuario staff puede aprobar
        self.user.is_company_admin = False
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.can_approve_documents())


class DocumentModelTest(TestCase):
    """Pruebas para el modelo Document."""
    
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
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user
        )
    
    def test_document_creation(self):
        """Prueba la creación de un documento."""
        self.assertEqual(self.document.company, self.company)
        self.assertEqual(self.document.entity, self.entity)
        self.assertEqual(self.document.name, "test.pdf")
        self.assertEqual(self.document.mime_type, "application/pdf")
        self.assertEqual(self.document.size_bytes, 1024)
        self.assertEqual(self.document.bucket_key, "test/test.pdf")
        self.assertEqual(self.document.created_by, self.user)
        self.assertIsNone(self.document.validation_status)
    
    def test_document_str(self):
        """Prueba la representación string del documento."""
        expected = "test.pdf (Empresa Test)"
        self.assertEqual(str(self.document), expected)
    
    def test_document_file_extension(self):
        """Prueba el método get_file_extension."""
        self.assertEqual(self.document.get_file_extension(), "pdf")
    
    def test_document_size_display(self):
        """Prueba el método get_size_display."""
        self.assertEqual(self.document.get_size_display(), "1.0 KB")
    
    def test_document_validation_status(self):
        """Prueba los métodos de estado de validación."""
        # Sin validación
        self.assertFalse(self.document.is_validated())
        self.assertFalse(self.document.is_pending())
        self.assertFalse(self.document.is_rejected())
        
        # Pendiente
        self.document.validation_status = 'P'
        self.document.save()
        self.assertFalse(self.document.is_validated())
        self.assertTrue(self.document.is_pending())
        self.assertFalse(self.document.is_rejected())
        
        # Aprobado
        self.document.validation_status = 'A'
        self.document.save()
        self.assertTrue(self.document.is_validated())
        self.assertFalse(self.document.is_pending())
        self.assertFalse(self.document.is_rejected())
        
        # Rechazado
        self.document.validation_status = 'R'
        self.document.save()
        self.assertFalse(self.document.is_validated())
        self.assertFalse(self.document.is_pending())
        self.assertTrue(self.document.is_rejected())


class ValidationFlowModelTest(TestCase):
    """Pruebas para el modelo ValidationFlow."""
    
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
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user
        )
        self.validation_flow = ValidationFlow.objects.create(
            document=self.document
        )
    
    def test_validation_flow_creation(self):
        """Prueba la creación de un flujo de validación."""
        self.assertEqual(self.validation_flow.document, self.document)
        self.assertTrue(self.validation_flow.is_active)
    
    def test_validation_flow_str(self):
        """Prueba la representación string del flujo de validación."""
        expected = "Flujo de validación para test.pdf"
        self.assertEqual(str(self.validation_flow), expected)
    
    def test_validation_flow_steps(self):
        """Prueba la gestión de pasos del flujo de validación."""
        # Crear pasos
        step1 = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user
        )
        step2 = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=2,
            approver=self.user
        )
        
        # Probar métodos
        steps = self.validation_flow.get_steps()
        self.assertEqual(len(steps), 2)
        
        pending_steps = self.validation_flow.get_pending_steps()
        self.assertEqual(len(pending_steps), 2)
        
        self.assertEqual(self.validation_flow.get_max_order(), 2)
    
    def test_validation_flow_completion(self):
        """Prueba la lógica de completado del flujo."""
        # Crear paso único
        step = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user
        )
        
        # Inicialmente no está completado
        self.assertFalse(self.validation_flow.is_completed())
        
        # Aprobar el paso
        step.status = 'A'
        step.save()
        
        # Ahora está completado
        self.assertTrue(self.validation_flow.is_completed())
    
    def test_validation_flow_rejection(self):
        """Prueba la lógica de rechazo del flujo."""
        # Crear paso
        step = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user
        )
        
        # Inicialmente no está rechazado
        self.assertFalse(self.validation_flow.is_rejected())
        
        # Rechazar el paso
        step.status = 'R'
        step.save()
        
        # Ahora está rechazado
        self.assertTrue(self.validation_flow.is_rejected())


class ValidationStepModelTest(TestCase):
    """Pruebas para el modelo ValidationStep."""
    
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
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user
        )
        self.validation_flow = ValidationFlow.objects.create(
            document=self.document
        )
        self.validation_step = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user
        )
    
    def test_validation_step_creation(self):
        """Prueba la creación de un paso de validación."""
        self.assertEqual(self.validation_step.validation_flow, self.validation_flow)
        self.assertEqual(self.validation_step.order, 1)
        self.assertEqual(self.validation_step.approver, self.user)
        self.assertEqual(self.validation_step.status, 'P')
    
    def test_validation_step_str(self):
        """Prueba la representación string del paso de validación."""
        expected = "Paso 1 - Test User"
        self.assertEqual(str(self.validation_step), expected)
    
    def test_validation_step_status_methods(self):
        """Prueba los métodos de estado del paso."""
        # Pendiente
        self.assertTrue(self.validation_step.is_pending())
        self.assertFalse(self.validation_step.is_approved())
        self.assertFalse(self.validation_step.is_rejected())
        
        # Aprobado
        self.validation_step.status = 'A'
        self.validation_step.save()
        self.assertFalse(self.validation_step.is_pending())
        self.assertTrue(self.validation_step.is_approved())
        self.assertFalse(self.validation_step.is_rejected())
        
        # Rechazado
        self.validation_step.status = 'R'
        self.validation_step.save()
        self.assertFalse(self.validation_step.is_pending())
        self.assertFalse(self.validation_step.is_approved())
        self.assertTrue(self.validation_step.is_rejected())


class ValidationActionModelTest(TestCase):
    """Pruebas para el modelo ValidationAction."""
    
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
        self.document = Document.objects.create(
            company=self.company,
            entity=self.entity,
            name="test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            bucket_key="test/test.pdf",
            created_by=self.user
        )
        self.validation_flow = ValidationFlow.objects.create(
            document=self.document
        )
        self.validation_step = ValidationStep.objects.create(
            validation_flow=self.validation_flow,
            order=1,
            approver=self.user
        )
        self.validation_action = ValidationAction.objects.create(
            document=self.document,
            validation_step=self.validation_step,
            actor=self.user,
            action='A',
            reason="Documento aprobado"
        )
    
    def test_validation_action_creation(self):
        """Prueba la creación de una acción de validación."""
        self.assertEqual(self.validation_action.document, self.document)
        self.assertEqual(self.validation_action.validation_step, self.validation_step)
        self.assertEqual(self.validation_action.actor, self.user)
        self.assertEqual(self.validation_action.action, 'A')
        self.assertEqual(self.validation_action.reason, "Documento aprobado")
    
    def test_validation_action_str(self):
        """Prueba la representación string de la acción de validación."""
        expected = "Aprobar - test.pdf por Test User"
        self.assertEqual(str(self.validation_action), expected)
    
    def test_validation_action_type_methods(self):
        """Prueba los métodos de tipo de acción."""
        # Aprobación
        self.assertTrue(self.validation_action.is_approval())
        self.assertFalse(self.validation_action.is_rejection())
        
        # Rechazo
        self.validation_action.action = 'R'
        self.validation_action.save()
        self.assertFalse(self.validation_action.is_approval())
        self.assertTrue(self.validation_action.is_rejection())
