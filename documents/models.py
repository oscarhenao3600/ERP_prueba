"""
Modelos para la gestión de documentos en el sistema ERP.

Este módulo contiene los modelos relacionados con documentos, flujos de validación
y acciones de aprobación, que son el núcleo del sistema de gestión de documentos.
"""

import uuid
import hashlib
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

User = get_user_model()


class Document(models.Model):
    """
    Modelo que representa un documento en el sistema ERP.
    
    Cada documento está asociado a una empresa y una entidad de negocio,
    y puede tener un flujo de validación jerárquico.
    """
    
    VALIDATION_STATUS_CHOICES = [
        (None, _("Sin validación")),
        ('P', _("Pendiente")),
        ('A', _("Aprobado")),
        ('R', _("Rechazado")),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del documento"
    )
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_("Empresa"),
        help_text="Empresa propietaria del documento"
    )
    
    entity = models.ForeignKey(
        'companies.Entity',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_("Entidad"),
        help_text="Entidad de negocio asociada al documento"
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nombre del archivo"),
        help_text="Nombre original del archivo"
    )
    
    mime_type = models.CharField(
        max_length=100,
        verbose_name=_("Tipo MIME"),
        help_text="Tipo MIME del archivo"
    )
    
    size_bytes = models.PositiveIntegerField(
        verbose_name=_("Tamaño en bytes"),
        help_text="Tamaño del archivo en bytes"
    )
    
    bucket_key = models.CharField(
        max_length=500,
        verbose_name=_("Clave del bucket"),
        help_text="Clave o ruta del archivo en el bucket de almacenamiento"
    )
    
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Hash del archivo"),
        help_text="Hash SHA-256 del archivo para verificación de integridad"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
        help_text="Descripción opcional del documento"
    )
    
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Etiquetas"),
        help_text="Etiquetas para categorizar el documento"
    )
    
    validation_status = models.CharField(
        max_length=1,
        choices=VALIDATION_STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Estado de validación"),
        help_text="Estado actual del proceso de validación"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_documents',
        verbose_name=_("Creado por"),
        help_text="Usuario que subió el documento"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de actualización")
    )
    
    class Meta:
        verbose_name = _("Documento")
        verbose_name_plural = _("Documentos")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'entity']),
            models.Index(fields=['validation_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['mime_type']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.company.name})"
    
    def get_file_extension(self):
        """Retorna la extensión del archivo."""
        return self.name.split('.')[-1].lower() if '.' in self.name else ''
    
    def get_size_display(self):
        """Retorna el tamaño del archivo en formato legible."""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def is_validated(self):
        """Indica si el documento está validado."""
        return self.validation_status == 'A'
    
    def is_pending(self):
        """Indica si el documento está pendiente de validación."""
        return self.validation_status == 'P'
    
    def is_rejected(self):
        """Indica si el documento fue rechazado."""
        return self.validation_status == 'R'
    
    def can_be_approved_by(self, user):
        """Indica si el usuario puede aprobar este documento."""
        if not user.can_approve_documents():
            return False
        
        # Verificar que el usuario pertenece a la misma empresa
        if user.company != self.company:
            return False
        
        # Verificar si hay un flujo de validación activo
        try:
            validation_flow = self.validation_flow
            return validation_flow.can_be_approved_by(user)
        except ValidationFlow.DoesNotExist:
            return False
    
    def can_be_rejected_by(self, user):
        """Indica si el usuario puede rechazar este documento."""
        if not user.can_approve_documents():
            return False
        
        # Verificar que el usuario pertenece a la misma empresa
        if user.company != self.company:
            return False
        
        # Verificar si hay un flujo de validación activo
        try:
            validation_flow = self.validation_flow
            return validation_flow.can_be_rejected_by(user)
        except ValidationFlow.DoesNotExist:
            return False


class ValidationFlow(models.Model):
    """
    Modelo que representa un flujo de validación jerárquico.
    
    Un flujo de validación define los pasos que debe seguir un documento
    para ser aprobado, con un orden jerárquico específico.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del flujo de validación"
    )
    
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='validation_flow',
        verbose_name=_("Documento"),
        help_text="Documento asociado al flujo de validación"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activo"),
        help_text="Indica si el flujo de validación está activo"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de actualización")
    )
    
    class Meta:
        verbose_name = _("Flujo de validación")
        verbose_name_plural = _("Flujos de validación")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Flujo de validación para {self.document.name}"
    
    def get_steps(self):
        """Retorna los pasos del flujo ordenados por orden."""
        return self.steps.all().order_by('order')
    
    def get_pending_steps(self):
        """Retorna los pasos pendientes de aprobación."""
        return self.steps.filter(status='P').order_by('order')
    
    def get_approved_steps(self):
        """Retorna los pasos aprobados."""
        return self.steps.filter(status='A').order_by('order')
    
    def get_rejected_steps(self):
        """Retorna los pasos rechazados."""
        return self.steps.filter(status='R').order_by('order')
    
    def get_max_order(self):
        """Retorna el orden máximo de los pasos."""
        return self.steps.aggregate(max_order=models.Max('order'))['max_order'] or 0
    
    def can_be_approved_by(self, user):
        """Indica si el usuario puede aprobar en este flujo."""
        if not self.is_active:
            return False
        
        # Verificar si el usuario es aprobador en algún paso
        return self.steps.filter(approver=user).exists()
    
    def can_be_rejected_by(self, user):
        """Indica si el usuario puede rechazar en este flujo."""
        if not self.is_active:
            return False
        
        # Cualquier aprobador puede rechazar
        return self.steps.filter(approver=user).exists()
    
    def is_completed(self):
        """Indica si el flujo está completado (todos los pasos aprobados)."""
        if not self.is_active:
            return False
        
        max_order = self.get_max_order()
        if max_order == 0:
            return False
        
        # Verificar si el paso de mayor orden está aprobado
        return self.steps.filter(order=max_order, status='A').exists()
    
    def is_rejected(self):
        """Indica si el flujo fue rechazado."""
        return self.steps.filter(status='R').exists()


class ValidationStep(models.Model):
    """
    Modelo que representa un paso individual en un flujo de validación.
    
    Cada paso tiene un orden jerárquico y un aprobador asignado.
    """
    
    STATUS_CHOICES = [
        ('P', _("Pendiente")),
        ('A', _("Aprobado")),
        ('R', _("Rechazado")),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del paso de validación"
    )
    
    validation_flow = models.ForeignKey(
        ValidationFlow,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_("Flujo de validación"),
        help_text="Flujo de validación al que pertenece el paso"
    )
    
    order = models.PositiveIntegerField(
        verbose_name=_("Orden"),
        help_text="Orden jerárquico del paso (mayor número = mayor jerarquía)"
    )
    
    approver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='validation_steps',
        verbose_name=_("Aprobador"),
        help_text="Usuario responsable de aprobar este paso"
    )
    
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='P',
        verbose_name=_("Estado"),
        help_text="Estado actual del paso"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de actualización")
    )
    
    class Meta:
        verbose_name = _("Paso de validación")
        verbose_name_plural = _("Pasos de validación")
        ordering = ['order']
        unique_together = ['validation_flow', 'order']
        indexes = [
            models.Index(fields=['validation_flow', 'order']),
            models.Index(fields=['status']),
            models.Index(fields=['approver']),
        ]
    
    def __str__(self):
        return f"Paso {self.order} - {self.approver.get_full_name()}"
    
    def is_pending(self):
        """Indica si el paso está pendiente."""
        return self.status == 'P'
    
    def is_approved(self):
        """Indica si el paso está aprobado."""
        return self.status == 'A'
    
    def is_rejected(self):
        """Indica si el paso está rechazado."""
        return self.status == 'R'


class ValidationAction(models.Model):
    """
    Modelo que registra las acciones de validación realizadas.
    
    Cada acción de aprobación o rechazo se registra para auditoría.
    """
    
    ACTION_CHOICES = [
        ('A', _("Aprobar")),
        ('R', _("Rechazar")),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único de la acción"
    )
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='validation_actions',
        verbose_name=_("Documento"),
        help_text="Documento sobre el que se realizó la acción"
    )
    
    validation_step = models.ForeignKey(
        ValidationStep,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_("Paso de validación"),
        help_text="Paso de validación sobre el que se realizó la acción"
    )
    
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='validation_actions',
        verbose_name=_("Actor"),
        help_text="Usuario que realizó la acción"
    )
    
    action = models.CharField(
        max_length=1,
        choices=ACTION_CHOICES,
        verbose_name=_("Acción"),
        help_text="Tipo de acción realizada"
    )
    
    reason = models.TextField(
        blank=True,
        verbose_name=_("Razón"),
        help_text="Razón o comentario de la acción"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    class Meta:
        verbose_name = _("Acción de validación")
        verbose_name_plural = _("Acciones de validación")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['validation_step']),
            models.Index(fields=['actor']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.document.name} por {self.actor.get_full_name()}"
    
    def is_approval(self):
        """Indica si la acción es una aprobación."""
        return self.action == 'A'
    
    def is_rejection(self):
        """Indica si la acción es un rechazo."""
        return self.action == 'R'
