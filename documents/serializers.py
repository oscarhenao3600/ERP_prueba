"""
Serializers para la API del sistema ERP de gestión de documentos.

Este módulo contiene los serializers de Django REST Framework para serializar
y deserializar los modelos del sistema, incluyendo validaciones personalizadas.
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Document, ValidationFlow, ValidationStep, ValidationAction
from companies.models import Company, Entity, EntityType, User

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Company."""
    
    users_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'legal_name', 'tax_id', 'email', 'phone', 'address',
            'is_active', 'created_at', 'updated_at', 'users_count', 'documents_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'users_count', 'documents_count']
    
    def get_users_count(self, obj):
        """Retorna el número de usuarios activos de la empresa."""
        return obj.get_active_users_count()
    
    def get_documents_count(self, obj):
        """Retorna el número de documentos de la empresa."""
        return obj.get_documents_count()


class EntityTypeSerializer(serializers.ModelSerializer):
    """Serializer para el modelo EntityType."""
    
    class Meta:
        model = EntityType
        fields = ['id', 'name', 'display_name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class EntitySerializer(serializers.ModelSerializer):
    """Serializer para el modelo Entity."""
    
    entity_type = EntityTypeSerializer(read_only=True)
    entity_type_id = serializers.UUIDField(write_only=True)
    documents_count = serializers.SerializerMethodField()
    pending_documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Entity
        fields = [
            'id', 'company', 'entity_type', 'entity_type_id', 'external_id', 'name',
            'metadata', 'is_active', 'created_at', 'updated_at', 'documents_count',
            'pending_documents_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'documents_count', 'pending_documents_count']
    
    def get_documents_count(self, obj):
        """Retorna el número de documentos asociados a la entidad."""
        return obj.get_documents_count()
    
    def get_pending_documents_count(self, obj):
        """Retorna el número de documentos pendientes de aprobación."""
        return obj.get_pending_documents_count()
    
    def validate_entity_type_id(self, value):
        """Valida que el tipo de entidad existe y está activo."""
        try:
            entity_type = EntityType.objects.get(id=value, is_active=True)
            return value
        except EntityType.DoesNotExist:
            raise serializers.ValidationError("Tipo de entidad no válido o inactivo")


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User."""
    
    company = CompanySerializer(read_only=True)
    company_id = serializers.UUIDField(write_only=True)
    full_name = serializers.SerializerMethodField()
    approval_actions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'company', 'company_id', 'employee_id', 'phone', 'position',
            'department', 'is_company_admin', 'is_active', 'created_at',
            'updated_at', 'approval_actions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approval_actions_count']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        """Retorna el nombre completo del usuario."""
        return obj.get_full_name()
    
    def get_approval_actions_count(self, obj):
        """Retorna el número de acciones de aprobación realizadas por el usuario."""
        return obj.get_approval_actions_count()
    
    def create(self, validated_data):
        """Crea un nuevo usuario con contraseña encriptada."""
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class ValidationStepSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ValidationStep."""
    
    approver = UserSerializer(read_only=True)
    approver_id = serializers.UUIDField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ValidationStep
        fields = [
            'id', 'order', 'approver', 'approver_id', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ValidationFlowSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ValidationFlow."""
    
    steps = ValidationStepSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    
    class Meta:
        model = ValidationFlow
        fields = [
            'id', 'document', 'is_active', 'is_completed', 'is_rejected',
            'created_at', 'updated_at', 'steps'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_completed', 'is_rejected']
    
    def get_is_completed(self, obj):
        """Indica si el flujo está completado."""
        return obj.is_completed()
    
    def get_is_rejected(self, obj):
        """Indica si el flujo fue rechazado."""
        return obj.is_rejected()


class ValidationActionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo ValidationAction."""
    
    actor = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ValidationAction
        fields = [
            'id', 'document', 'validation_step', 'actor', 'action', 'action_display',
            'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Document."""
    
    company = CompanySerializer(read_only=True)
    entity = EntitySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    validation_flow = ValidationFlowSerializer(read_only=True)
    validation_status_display = serializers.CharField(source='get_validation_status_display', read_only=True)
    file_extension = serializers.SerializerMethodField()
    size_display = serializers.SerializerMethodField()
    is_validated = serializers.SerializerMethodField()
    is_pending = serializers.SerializerMethodField()
    is_rejected = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'company', 'entity', 'name', 'mime_type', 'size_bytes', 'size_display',
            'bucket_key', 'file_hash', 'description', 'tags', 'validation_status',
            'validation_status_display', 'validation_flow', 'created_by', 'created_at',
            'updated_at', 'file_extension', 'is_validated', 'is_pending', 'is_rejected'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'file_extension', 'size_display',
            'is_validated', 'is_pending', 'is_rejected'
        ]
    
    def get_file_extension(self, obj):
        """Retorna la extensión del archivo."""
        return obj.get_file_extension()
    
    def get_size_display(self, obj):
        """Retorna el tamaño del archivo en formato legible."""
        return obj.get_size_display()
    
    def get_is_validated(self, obj):
        """Indica si el documento está validado."""
        return obj.is_validated()
    
    def get_is_pending(self, obj):
        """Indica si el documento está pendiente de validación."""
        return obj.is_pending()
    
    def get_is_rejected(self, obj):
        """Indica si el documento fue rechazado."""
        return obj.is_rejected()


class DocumentCreateSerializer(serializers.Serializer):
    """
    Serializer para crear documentos con flujo de validación.
    
    Este serializer maneja la creación de documentos con metadatos y
    opcionalmente un flujo de validación jerárquico.
    """
    
    company_id = serializers.UUIDField()
    entity = serializers.DictField()
    document = serializers.DictField()
    validation_flow = serializers.DictField(required=False)
    
    def validate_company_id(self, value):
        """Valida que la empresa existe y está activa."""
        try:
            company = Company.objects.get(id=value, is_active=True)
            return value
        except Company.DoesNotExist:
            raise serializers.ValidationError("Empresa no válida o inactiva")
    
    def validate_entity(self, value):
        """Valida los datos de la entidad."""
        required_fields = ['entity_type', 'entity_id']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' requerido en entity")
        
        # Validar que la entidad existe
        try:
            entity = Entity.objects.get(
                company_id=self.initial_data['company_id'],
                entity_type__name=value['entity_type'],
                external_id=value['entity_id'],
                is_active=True
            )
            return value
        except Entity.DoesNotExist:
            raise serializers.ValidationError("Entidad no válida o inactiva")
    
    def validate_document(self, value):
        """Valida los datos del documento."""
        required_fields = ['name', 'mime_type', 'size_bytes', 'bucket_key']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' requerido en document")
        
        # Validar tipo MIME
        from django.conf import settings
        if value['mime_type'] not in settings.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(f"Tipo MIME '{value['mime_type']}' no permitido")
        
        # Validar tamaño
        if value['size_bytes'] > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(f"Tamaño de archivo excede el máximo permitido")
        
        return value
    
    def validate_validation_flow(self, value):
        """Valida los datos del flujo de validación."""
        if not value.get('enabled', False):
            return value
        
        steps = value.get('steps', [])
        if not steps:
            raise serializers.ValidationError("Debe proporcionar al menos un paso de validación")
        
        # Validar que no hay órdenes duplicados
        orders = [step['order'] for step in steps]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError("No puede haber pasos con el mismo orden")
        
        # Validar que los aprobadores existen
        for step in steps:
            try:
                User.objects.get(id=step['approver_user_id'])
            except User.DoesNotExist:
                raise serializers.ValidationError(f"Aprobador {step['approver_user_id']} no existe")
        
        return value


class DocumentApprovalSerializer(serializers.Serializer):
    """Serializer para aprobar documentos."""
    
    actor_user_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_actor_user_id(self, value):
        """Valida que el usuario actor existe."""
        try:
            user = User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no válido o inactivo")


class DocumentRejectionSerializer(serializers.Serializer):
    """Serializer para rechazar documentos."""
    
    actor_user_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_actor_user_id(self, value):
        """Valida que el usuario actor existe."""
        try:
            user = User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario no válido o inactivo")


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer para generar URLs pre-firmadas de subida.
    
    Este serializer genera las URLs pre-firmadas necesarias para subir
    archivos directamente al bucket de almacenamiento.
    """
    
    company_id = serializers.UUIDField()
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    filename = serializers.CharField()
    mime_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    
    def validate_company_id(self, value):
        """Valida que la empresa existe y está activa."""
        try:
            Company.objects.get(id=value, is_active=True)
            return value
        except Company.DoesNotExist:
            raise serializers.ValidationError("Empresa no válida o inactiva")
    
    def validate_mime_type(self, value):
        """Valida el tipo MIME."""
        from django.conf import settings
        if value not in settings.ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(f"Tipo MIME '{value}' no permitido")
        return value
    
    def validate_size_bytes(self, value):
        """Valida el tamaño del archivo."""
        from django.conf import settings
        if value > settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(f"Tamaño de archivo excede el máximo permitido")
        return value
