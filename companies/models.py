"""
Modelos para la gestión de empresas en el sistema ERP de documentos.

Este módulo contiene los modelos relacionados con empresas y usuarios,
que son la base para el control de acceso y organización de documentos.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    """
    Modelo que representa una empresa en el sistema ERP.
    
    Cada empresa tiene sus propios documentos y usuarios asociados.
    Los documentos están organizados por empresa para mantener la separación
    de datos entre diferentes organizaciones.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único de la empresa"
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nombre de la empresa"),
        help_text="Nombre comercial de la empresa"
    )
    
    legal_name = models.CharField(
        max_length=255,
        verbose_name=_("Razón social"),
        help_text="Razón social oficial de la empresa"
    )
    
    tax_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("NIT/RUT"),
        help_text="Número de identificación tributaria",
        validators=[
            RegexValidator(
                regex=r'^[0-9\-\.]+$',
                message=_("El NIT debe contener solo números, guiones y puntos")
            )
        ]
    )
    
    email = models.EmailField(
        verbose_name=_("Email de contacto"),
        help_text="Email principal de contacto de la empresa"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Teléfono"),
        help_text="Número de teléfono de contacto"
    )
    
    address = models.TextField(
        blank=True,
        verbose_name=_("Dirección"),
        help_text="Dirección física de la empresa"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activa"),
        help_text="Indica si la empresa está activa en el sistema"
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
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")
        ordering = ['name']
        indexes = [
            models.Index(fields=['tax_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tax_id})"
    
    def get_active_users_count(self):
        """Retorna el número de usuarios activos de la empresa."""
        return self.users.filter(is_active=True).count()
    
    def get_documents_count(self):
        """Retorna el número de documentos de la empresa."""
        return self.documents.count()


class User(AbstractUser):
    """
    Modelo de usuario extendido que incluye información de empresa.
    
    Hereda de AbstractUser para mantener compatibilidad con Django
    y añade campos específicos para el sistema ERP.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del usuario"
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_("Empresa"),
        help_text="Empresa a la que pertenece el usuario"
    )
    
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("ID de empleado"),
        help_text="Identificador del empleado en la empresa"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Teléfono"),
        help_text="Número de teléfono del usuario"
    )
    
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Cargo"),
        help_text="Cargo o posición del usuario en la empresa"
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Departamento"),
        help_text="Departamento al que pertenece el usuario"
    )
    
    is_company_admin = models.BooleanField(
        default=False,
        verbose_name=_("Administrador de empresa"),
        help_text="Indica si el usuario es administrador de la empresa"
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
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_company_admin']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.company.name})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def can_approve_documents(self):
        """Indica si el usuario puede aprobar documentos."""
        return self.is_active and (self.is_company_admin or self.is_staff)
    
    def get_approval_actions_count(self):
        """Retorna el número de acciones de aprobación realizadas por el usuario."""
        from documents.models import ValidationAction
        return ValidationAction.objects.filter(actor=self).count()


class EntityType(models.Model):
    """
    Modelo que define los tipos de entidades de negocio.
    
    Las entidades representan objetos del dominio de negocio a los que
    se pueden asociar documentos (vehículos, empleados, contratos, etc.).
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del tipo de entidad"
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nombre"),
        help_text="Nombre del tipo de entidad (ej: vehicle, employee, contract)"
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name=_("Nombre para mostrar"),
        help_text="Nombre legible para mostrar en la interfaz"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
        help_text="Descripción del tipo de entidad"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activo"),
        help_text="Indica si el tipo de entidad está activo"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de creación")
    )
    
    class Meta:
        verbose_name = _("Tipo de entidad")
        verbose_name_plural = _("Tipos de entidad")
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.display_name


class Entity(models.Model):
    """
    Modelo que representa una entidad de negocio genérica.
    
    Las entidades son objetos del dominio de negocio a los que se pueden
    asociar documentos. Este modelo genérico permite asociar documentos
    a cualquier tipo de entidad sin necesidad de crear modelos específicos.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único de la entidad"
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='entities',
        verbose_name=_("Empresa"),
        help_text="Empresa a la que pertenece la entidad"
    )
    
    entity_type = models.ForeignKey(
        EntityType,
        on_delete=models.CASCADE,
        related_name='entities',
        verbose_name=_("Tipo de entidad"),
        help_text="Tipo de entidad de negocio"
    )
    
    external_id = models.CharField(
        max_length=100,
        verbose_name=_("ID externo"),
        help_text="Identificador de la entidad en el sistema externo"
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Nombre"),
        help_text="Nombre o descripción de la entidad"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadatos"),
        help_text="Información adicional de la entidad en formato JSON"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activa"),
        help_text="Indica si la entidad está activa"
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
        verbose_name = _("Entidad")
        verbose_name_plural = _("Entidades")
        ordering = ['name']
        unique_together = ['company', 'entity_type', 'external_id']
        indexes = [
            models.Index(fields=['company', 'entity_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.entity_type.display_name})"
    
    def get_documents_count(self):
        """Retorna el número de documentos asociados a la entidad."""
        return self.documents.count()
    
    def get_pending_documents_count(self):
        """Retorna el número de documentos pendientes de aprobación."""
        return self.documents.filter(validation_status='P').count()
