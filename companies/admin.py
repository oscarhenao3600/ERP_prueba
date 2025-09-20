"""
Configuración del admin de Django para la aplicación de empresas.

Este módulo registra los modelos de empresas en el admin de Django
para facilitar la administración desde la interfaz web.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Company, Entity, EntityType, User


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin para el modelo Company."""
    
    list_display = [
        'name', 'legal_name', 'tax_id', 'email', 'is_active',
        'users_count', 'documents_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'legal_name', 'tax_id', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'legal_name', 'tax_id')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def users_count(self, obj):
        """Muestra el número de usuarios con enlace."""
        count = obj.get_active_users_count()
        if count > 0:
            url = reverse('admin:companies_user_changelist') + f'?company__id__exact={obj.id}'
            return format_html('<a href="{}">{} usuarios</a>', url, count)
        return '0 usuarios'
    users_count.short_description = 'Usuarios'
    
    def documents_count(self, obj):
        """Muestra el número de documentos con enlace."""
        count = obj.get_documents_count()
        if count > 0:
            url = reverse('admin:documents_document_changelist') + f'?company__id__exact={obj.id}'
            return format_html('<a href="{}">{} documentos</a>', url, count)
        return '0 documentos'
    documents_count.short_description = 'Documentos'


@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    """Admin para el modelo EntityType."""
    
    list_display = ['name', 'display_name', 'is_active', 'entities_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['id', 'created_at']
    
    def entities_count(self, obj):
        """Muestra el número de entidades de este tipo."""
        count = obj.entities.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:companies_entity_changelist') + f'?entity_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} entidades</a>', url, count)
        return '0 entidades'
    entities_count.short_description = 'Entidades'


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Admin para el modelo Entity."""
    
    list_display = [
        'name', 'company', 'entity_type', 'external_id',
        'is_active', 'documents_count', 'created_at'
    ]
    list_filter = ['is_active', 'entity_type', 'company', 'created_at']
    search_fields = ['name', 'external_id', 'company__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'company', 'entity_type', 'external_id', 'name')
        }),
        ('Metadatos', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def documents_count(self, obj):
        """Muestra el número de documentos con enlace."""
        count = obj.get_documents_count()
        if count > 0:
            url = reverse('admin:documents_document_changelist') + f'?entity__id__exact={obj.id}'
            return format_html('<a href="{}">{} documentos</a>', url, count)
        return '0 documentos'
    documents_count.short_description = 'Documentos'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin para el modelo User."""
    
    list_display = [
        'username', 'email', 'full_name', 'company', 'is_company_admin',
        'is_active', 'approval_actions_count', 'created_at'
    ]
    list_filter = ['is_active', 'is_company_admin', 'company', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'company__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login', 'date_joined']
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'username', 'email', 'first_name', 'last_name')
        }),
        ('Empresa', {
            'fields': ('company', 'employee_id', 'position', 'department')
        }),
        ('Contacto', {
            'fields': ('phone',)
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_company_admin', 'is_staff', 'is_superuser')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    def approval_actions_count(self, obj):
        """Muestra el número de acciones de aprobación con enlace."""
        count = obj.get_approval_actions_count()
        if count > 0:
            url = reverse('admin:documents_validationaction_changelist') + f'?actor__id__exact={obj.id}'
            return format_html('<a href="{}">{} acciones</a>', url, count)
        return '0 acciones'
    approval_actions_count.short_description = 'Acciones de Aprobación'
    
    def full_name(self, obj):
        """Muestra el nombre completo del usuario."""
        return obj.get_full_name()
    full_name.short_description = 'Nombre Completo'
