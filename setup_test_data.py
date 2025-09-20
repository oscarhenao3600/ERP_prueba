#!/usr/bin/env python
"""
Script para crear datos de prueba del sistema ERP de gestión de documentos.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_documents.settings.development')
django.setup()

from companies.models import Company, EntityType, Entity, User

def create_test_data():
    """Crear datos de prueba para el sistema."""
    
    print("🔧 Creando datos de prueba...")
    
    # Obtener empresa existente
    company = Company.objects.first()
    if not company:
        print("❌ No se encontró empresa. Creando una nueva...")
        company = Company.objects.create(
            name='Empresa de Prueba',
            legal_name='Empresa de Prueba S.A.S.',
            tax_id='900123456-1',
            email='prueba@empresa.com',
            phone='+57-1-234-5678',
            address='Calle 123 #45-67, Bogotá, Colombia'
        )
    
    print(f"✅ Usando empresa: {company.name}")
    
    # Crear tipos de entidad
    vehicle_type, created = EntityType.objects.get_or_create(
        name='vehicle',
        defaults={
            'display_name': 'Vehículo',
            'description': 'Vehículos de la empresa',
            'is_active': True
        }
    )
    
    employee_type, created = EntityType.objects.get_or_create(
        name='employee',
        defaults={
            'display_name': 'Empleado',
            'description': 'Empleados de la empresa',
            'is_active': True
        }
    )
    
    print(f"✅ Tipos de entidad: {vehicle_type.name}, {employee_type.name}")
    
    # Crear entidades de prueba
    vehicle, created = Entity.objects.get_or_create(
        company=company,
        entity_type=vehicle_type,
        external_id='VEH001',
        defaults={
            'name': 'Vehículo de Prueba',
            'metadata': '{"modelo": "Toyota Corolla", "placa": "ABC123"}',
            'is_active': True
        }
    )
    
    employee, created = Entity.objects.get_or_create(
        company=company,
        entity_type=employee_type,
        external_id='EMP001',
        defaults={
            'name': 'Juan Pérez',
            'metadata': '{"cargo": "Desarrollador", "salario": 5000000}',
            'is_active': True
        }
    )
    
    print(f"✅ Entidades creadas: {vehicle.name}, {employee.name}")
    
    # Crear usuarios de prueba
    user1, created = User.objects.get_or_create(
        username='test_user1',
        defaults={
            'email': 'user1@test.com',
            'password': 'pbkdf2_sha256$600000$test$test',  # Password: test123
            'company': company,
            'employee_id': 'EMP001',
            'phone': '+57-1-234-5679',
            'position': 'Aprobador',
            'department': 'Recursos Humanos',
            'is_company_admin': False,
            'is_staff': False,
            'is_active': True
        }
    )
    
    user2, created = User.objects.get_or_create(
        username='test_user2',
        defaults={
            'email': 'user2@test.com',
            'password': 'pbkdf2_sha256$600000$test$test',  # Password: test123
            'company': company,
            'employee_id': 'EMP002',
            'phone': '+57-1-234-5680',
            'position': 'Gerente',
            'department': 'Administración',
            'is_company_admin': True,
            'is_staff': False,
            'is_active': True
        }
    )
    
    print(f"✅ Usuarios de prueba creados: {user1.username}, {user2.username}")
    
    print("\n🎉 Datos de prueba creados exitosamente!")
    print("\n📋 Credenciales de prueba:")
    print("   Admin: admin / admin123")
    print("   User1: test_user1 / test123")
    print("   User2: test_user2 / test123")

if __name__ == '__main__':
    create_test_data()
