"""
Lógica de validación jerárquica para documentos en el sistema ERP.

Este módulo contiene la lógica de negocio para el flujo de validación jerárquico,
incluyendo las reglas de aprobación automática y manejo de rechazos.
"""

from typing import List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import logging

from .models import Document, ValidationFlow, ValidationStep, ValidationAction
from companies.models import User

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Servicio para manejar la lógica de validación jerárquica de documentos.
    
    Implementa las reglas de negocio para el flujo de validación:
    - Aprobación automática de pasos previos cuando un aprobador de mayor jerarquía aprueba
    - Rechazo terminal que marca el documento como rechazado
    - Completado del flujo cuando el último paso es aprobado
    """
    
    @staticmethod
    def create_validation_flow(document: Document, steps_data: List[dict]) -> ValidationFlow:
        """
        Crea un flujo de validación para un documento.
        
        Args:
            document: Documento al que se aplicará el flujo
            steps_data: Lista de pasos con orden y aprobador
            
        Returns:
            Flujo de validación creado
            
        Raises:
            ValidationError: Si los datos de los pasos son inválidos
        """
        if not steps_data:
            raise ValidationError("Debe proporcionar al menos un paso de validación")
        
        # Validar que no hay pasos duplicados
        orders = [step['order'] for step in steps_data]
        if len(orders) != len(set(orders)):
            raise ValidationError("No puede haber pasos con el mismo orden")
        
        # Validar que los aprobadores pertenecen a la misma empresa
        for step_data in steps_data:
            approver = User.objects.get(id=step_data['approver_user_id'])
            if approver.company != document.company:
                raise ValidationError(f"El aprobador {approver.get_full_name()} no pertenece a la empresa del documento")
        
        with transaction.atomic():
            # Crear el flujo de validación
            validation_flow = ValidationFlow.objects.create(
                document=document
            )
            
            # Crear los pasos de validación
            for step_data in steps_data:
                ValidationStep.objects.create(
                    validation_flow=validation_flow,
                    order=step_data['order'],
                    approver_id=step_data['approver_user_id']
                )
            
            # Marcar el documento como pendiente
            document.validation_status = 'P'
            document.save()
            
            logger.info(f"Flujo de validación creado para documento {document.id} con {len(steps_data)} pasos")
            
            return validation_flow
    
    @staticmethod
    def approve_document(document: Document, actor: User, reason: str = "") -> ValidationAction:
        """
        Aprueba un documento siguiendo las reglas de jerarquía.
        
        Args:
            document: Documento a aprobar
            actor: Usuario que realiza la aprobación
            reason: Razón de la aprobación
            
        Returns:
            Acción de validación creada
            
        Raises:
            ValidationError: Si el usuario no puede aprobar el documento
        """
        if not document.can_be_approved_by(actor):
            raise ValidationError("El usuario no tiene permisos para aprobar este documento")
        
        try:
            validation_flow = document.validation_flow
        except ValidationFlow.DoesNotExist:
            raise ValidationError("El documento no tiene un flujo de validación activo")
        
        if not validation_flow.is_active:
            raise ValidationError("El flujo de validación no está activo")
        
        if document.is_rejected():
            raise ValidationError("No se puede aprobar un documento rechazado")
        
        if document.is_validated():
            raise ValidationError("El documento ya está aprobado")
        
        with transaction.atomic():
            # Encontrar el paso del actor
            actor_step = validation_flow.steps.filter(approver=actor).first()
            if not actor_step:
                raise ValidationError("El usuario no es aprobador en este flujo de validación")
            
            if actor_step.is_approved():
                raise ValidationError("El usuario ya aprobó este paso")
            
            if actor_step.is_rejected():
                raise ValidationError("Este paso ya fue rechazado")
            
            # Aprobar el paso del actor
            actor_step.status = 'A'
            actor_step.save()
            
            # Crear la acción de aprobación
            action = ValidationAction.objects.create(
                document=document,
                validation_step=actor_step,
                actor=actor,
                action='A',
                reason=reason
            )
            
            # Aplicar regla de jerarquía: aprobar pasos previos pendientes
            ValidationService._approve_previous_steps(validation_flow, actor_step.order)
            
            # Verificar si el flujo está completado
            if ValidationService._is_flow_completed(validation_flow):
                document.validation_status = 'A'
                document.save()
                logger.info(f"Documento {document.id} aprobado completamente")
            else:
                logger.info(f"Paso {actor_step.order} aprobado para documento {document.id}")
            
            return action
    
    @staticmethod
    def reject_document(document: Document, actor: User, reason: str = "") -> ValidationAction:
        """
        Rechaza un documento (acción terminal).
        
        Args:
            document: Documento a rechazar
            actor: Usuario que realiza el rechazo
            reason: Razón del rechazo
            
        Returns:
            Acción de validación creada
            
        Raises:
            ValidationError: Si el usuario no puede rechazar el documento
        """
        if not document.can_be_rejected_by(actor):
            raise ValidationError("El usuario no tiene permisos para rechazar este documento")
        
        try:
            validation_flow = document.validation_flow
        except ValidationFlow.DoesNotExist:
            raise ValidationError("El documento no tiene un flujo de validación activo")
        
        if not validation_flow.is_active:
            raise ValidationError("El flujo de validación no está activo")
        
        if document.is_rejected():
            raise ValidationError("El documento ya está rechazado")
        
        if document.is_validated():
            raise ValidationError("No se puede rechazar un documento ya aprobado")
        
        with transaction.atomic():
            # Encontrar el paso del actor
            actor_step = validation_flow.steps.filter(approver=actor).first()
            if not actor_step:
                raise ValidationError("El usuario no es aprobador en este flujo de validación")
            
            if actor_step.is_rejected():
                raise ValidationError("Este paso ya fue rechazado")
            
            # Rechazar el paso del actor
            actor_step.status = 'R'
            actor_step.save()
            
            # Crear la acción de rechazo
            action = ValidationAction.objects.create(
                document=document,
                validation_step=actor_step,
                actor=actor,
                action='R',
                reason=reason
            )
            
            # Marcar el documento como rechazado (acción terminal)
            document.validation_status = 'R'
            document.save()
            
            # Desactivar el flujo de validación
            validation_flow.is_active = False
            validation_flow.save()
            
            logger.info(f"Documento {document.id} rechazado por {actor.get_full_name()}")
            
            return action
    
    @staticmethod
    def _approve_previous_steps(validation_flow: ValidationFlow, current_order: int) -> None:
        """
        Aprueba automáticamente los pasos previos pendientes.
        
        Args:
            validation_flow: Flujo de validación
            current_order: Orden del paso actual
        """
        # Obtener pasos previos pendientes
        previous_steps = validation_flow.steps.filter(
            order__lt=current_order,
            status='P'
        )
        
        for step in previous_steps:
            step.status = 'A'
            step.save()
            logger.info(f"Paso {step.order} aprobado automáticamente por jerarquía")
    
    @staticmethod
    def _is_flow_completed(validation_flow: ValidationFlow) -> bool:
        """
        Verifica si el flujo de validación está completado.
        
        Args:
            validation_flow: Flujo de validación
            
        Returns:
            True si el flujo está completado
        """
        max_order = validation_flow.get_max_order()
        if max_order == 0:
            return False
        
        # El flujo está completado si el paso de mayor orden está aprobado
        return validation_flow.steps.filter(order=max_order, status='A').exists()
    
    @staticmethod
    def get_validation_status(document: Document) -> dict:
        """
        Obtiene el estado detallado del flujo de validación de un documento.
        
        Args:
            document: Documento
            
        Returns:
            Diccionario con el estado del flujo de validación
        """
        try:
            validation_flow = document.validation_flow
        except ValidationFlow.DoesNotExist:
            return {
                'has_validation': False,
                'status': document.validation_status,
                'steps': []
            }
        
        steps = []
        for step in validation_flow.get_steps():
            steps.append({
                'order': step.order,
                'approver': {
                    'id': step.approver.id,
                    'name': step.approver.get_full_name(),
                    'email': step.approver.email
                },
                'status': step.status,
                'status_display': step.get_status_display(),
                'created_at': step.created_at,
                'updated_at': step.updated_at
            })
        
        return {
            'has_validation': True,
            'status': document.validation_status,
            'is_active': validation_flow.is_active,
            'is_completed': validation_flow.is_completed(),
            'is_rejected': validation_flow.is_rejected(),
            'steps': steps,
            'created_at': validation_flow.created_at,
            'updated_at': validation_flow.updated_at
        }
    
    @staticmethod
    def get_pending_approvals_for_user(user: User) -> List[Document]:
        """
        Obtiene los documentos pendientes de aprobación para un usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Lista de documentos pendientes de aprobación
        """
        return Document.objects.filter(
            company=user.company,
            validation_status='P',
            validation_flow__is_active=True,
            validation_flow__steps__approver=user,
            validation_flow__steps__status='P'
        ).distinct()
    
    @staticmethod
    def get_user_approval_stats(user: User) -> dict:
        """
        Obtiene estadísticas de aprobaciones para un usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Diccionario con estadísticas de aprobaciones
        """
        from django.db.models import Count
        
        # Documentos aprobados por el usuario
        approved_count = ValidationAction.objects.filter(
            actor=user,
            action='A'
        ).count()
        
        # Documentos rechazados por el usuario
        rejected_count = ValidationAction.objects.filter(
            actor=user,
            action='R'
        ).count()
        
        # Documentos pendientes de aprobación
        pending_count = ValidationService.get_pending_approvals_for_user(user).count()
        
        return {
            'approved': approved_count,
            'rejected': rejected_count,
            'pending': pending_count,
            'total_actions': approved_count + rejected_count
        }
