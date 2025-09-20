"""
Configuración del admin de Django para la aplicación de documentos.

Este módulo registra los modelos de documentos en el admin de Django
para facilitar la administración desde la interfaz web.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Document, ValidationFlow, ValidationStep, ValidationAction


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin para el modelo Document."""
    
    list_display = [
        'name', 'company', 'entity', 'mime_type', 'size_display',
        'validation_status_display', 'created_by', 'created_at'
    ]
    list_filter = [
        'validation_status', 'mime_type', 'company', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'company__name', 'entity__name', 'created_by__username'
    ]
    readonly_fields = [
        'id', 'file_hash', 'created_at', 'updated_at', 'size_display', 'file_extension'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'company', 'entity', 'name', 'description')
        }),
        ('Archivo', {
            'fields': ('mime_type', 'size_bytes', 'size_display', 'file_extension', 'bucket_key', 'file_hash')
        }),
        ('Metadatos', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        ('Validación', {
            'fields': ('validation_status',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def size_display(self, obj):
        """Muestra el tamaño del archivo en formato legible."""
        return obj.get_size_display()
    size_display.short_description = 'Tamaño'
    
    def file_extension(self, obj):
        """Muestra la extensión del archivo."""
        return obj.get_file_extension()
    file_extension.short_description = 'Extensión'
    
    def validation_status_display(self, obj):
        """Muestra el estado de validación con colores."""
        status = obj.validation_status
        if status == 'A':
            return format_html('<span style="color: green;">✓ Aprobado</span>')
        elif status == 'R':
            return format_html('<span style="color: red;">✗ Rechazado</span>')
        elif status == 'P':
            return format_html('<span style="color: orange;">⏳ Pendiente</span>')
        else:
            return format_html('<span style="color: gray;">- Sin validación</span>')
    validation_status_display.short_description = 'Estado de Validación'


@admin.register(ValidationFlow)
class ValidationFlowAdmin(admin.ModelAdmin):
    """Admin para el modelo ValidationFlow."""
    
    list_display = [
        'document', 'is_active', 'is_completed', 'is_rejected',
        'steps_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['document__name', 'document__company__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_completed', 'is_rejected']
    
    def steps_count(self, obj):
        """Muestra el número de pasos con enlace."""
        count = obj.steps.count()
        if count > 0:
            url = reverse('admin:documents_validationstep_changelist') + f'?validation_flow__id__exact={obj.id}'
            return format_html('<a href="{}">{} pasos</a>', url, count)
        return '0 pasos'
    steps_count.short_description = 'Pasos'
    
    def is_completed(self, obj):
        """Muestra si el flujo está completado."""
        return obj.is_completed()
    is_completed.short_description = 'Completado'
    is_completed.boolean = True
    
    def is_rejected(self, obj):
        """Muestra si el flujo fue rechazado."""
        return obj.is_rejected()
    is_rejected.short_description = 'Rechazado'
    is_rejected.boolean = True


@admin.register(ValidationStep)
class ValidationStepAdmin(admin.ModelAdmin):
    """Admin para el modelo ValidationStep."""
    
    list_display = [
        'validation_flow', 'order', 'approver', 'status_display',
        'actions_count', 'created_at'
    ]
    list_filter = ['status', 'validation_flow__is_active', 'created_at']
    search_fields = [
        'approver__username', 'approver__email', 'validation_flow__document__name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'actions_count']
    
    def status_display(self, obj):
        """Muestra el estado del paso con colores."""
        if obj.status == 'A':
            return format_html('<span style="color: green;">✓ Aprobado</span>')
        elif obj.status == 'R':
            return format_html('<span style="color: red;">✗ Rechazado</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendiente</span>')
    status_display.short_description = 'Estado'
    
    def actions_count(self, obj):
        """Muestra el número de acciones con enlace."""
        count = obj.actions.count()
        if count > 0:
            url = reverse('admin:documents_validationaction_changelist') + f'?validation_step__id__exact={obj.id}'
            return format_html('<a href="{}">{} acciones</a>', url, count)
        return '0 acciones'
    actions_count.short_description = 'Acciones'


@admin.register(ValidationAction)
class ValidationActionAdmin(admin.ModelAdmin):
    """Admin para el modelo ValidationAction."""
    
    list_display = [
        'document', 'validation_step', 'actor', 'action_display',
        'reason_short', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = [
        'document__name', 'actor__username', 'actor__email', 'reason'
    ]
    readonly_fields = ['id', 'created_at']
    
    def action_display(self, obj):
        """Muestra la acción con colores."""
        if obj.action == 'A':
            return format_html('<span style="color: green;">✓ Aprobar</span>')
        else:
            return format_html('<span style="color: red;">✗ Rechazar</span>')
    action_display.short_description = 'Acción'
    
    def reason_short(self, obj):
        """Muestra una versión corta de la razón."""
        if obj.reason:
            return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
        return '-'
    reason_short.short_description = 'Razón'
    
    def has_add_permission(self, request):
        """Las acciones de validación no se pueden crear manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Las acciones de validación no se pueden modificar."""
        return False
