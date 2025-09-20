"""
Serializers para la aplicación de empresas.

Este módulo contiene los serializers para los modelos de empresas,
entidades y usuarios del sistema ERP.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Company, Entity, EntityType, User

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
