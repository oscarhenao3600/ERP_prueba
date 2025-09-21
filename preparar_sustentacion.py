#!/usr/bin/env python
"""
Script para preparar el entorno de sustentación del sistema ERP.

Este script configura automáticamente todos los datos necesarios
para realizar una sustentación completa del sistema.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def setup_django():
    """Configura Django para el script."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_documents.settings.development')
    django.setup()

def preparar_datos_sustentacion():
    """Prepara todos los datos necesarios para la sustentación."""
    print("🚀 PREPARANDO ENTORNO DE SUSTENTACIÓN")
    print("=" * 50)
    
    from companies.models import Company, User, Entity, EntityType
    from documents.models import Document
    from django.contrib.auth.hashers import make_password
    
    # 1. Verificar/Crear empresa de sustentación
    empresa, created = Company.objects.get_or_create(
        tax_id="900999888-7",
        defaults={
            'name': 'Empresa Sustentación Demo',
            'legal_name': 'Empresa Sustentación Demo S.A.S.',
            'email': 'demo@sustentacion.com',
            'phone': '+57 300 123 4567',
            'address': 'Calle Demo #123-45, Bogotá, Colombia'
        }
    )
    
    if created:
        print("✅ Empresa de sustentación creada")
    else:
        print("✅ Empresa de sustentación ya existe")
    
    # 2. Verificar/Crear tipos de entidad
    tipos_entidad = [
        {
            'name': 'vehicle',
            'display_name': 'Vehículo',
            'description': 'Vehículos de la empresa'
        },
        {
            'name': 'employee',
            'display_name': 'Empleado',
            'description': 'Empleados de la empresa'
        }
    ]
    
    for tipo_data in tipos_entidad:
        tipo, created = EntityType.objects.get_or_create(
            name=tipo_data['name'],
            defaults=tipo_data
        )
        if created:
            print(f"✅ Tipo de entidad '{tipo_data['name']}' creado")
        else:
            print(f"✅ Tipo de entidad '{tipo_data['name']}' ya existe")
    
    # 3. Crear usuarios de sustentación
    usuarios_data = [
        {
            'username': 'sustentador',
            'email': 'sustentador@demo.com',
            'password': 'sustentacion123',
            'first_name': 'Usuario',
            'last_name': 'Sustentador',
            'employee_id': 'EMP-SUST-001',
            'phone': '+57 300 111 1111',
            'position': 'Analista de Documentos',
            'department': 'Gestión Documental'
        },
        {
            'username': 'aprobador1',
            'email': 'aprobador1@demo.com',
            'password': 'aprobador123',
            'first_name': 'Carlos',
            'last_name': 'Aprobador',
            'employee_id': 'EMP-APPR-001',
            'phone': '+57 300 222 2222',
            'position': 'Supervisor de Documentos',
            'department': 'Gestión Documental'
        },
        {
            'username': 'aprobador2',
            'email': 'aprobador2@demo.com',
            'password': 'aprobador123',
            'first_name': 'Ana',
            'last_name': 'Revisora',
            'employee_id': 'EMP-APPR-002',
            'phone': '+57 300 333 3333',
            'position': 'Gerente de Documentos',
            'department': 'Gestión Documental'
        }
    ]
    
    for user_data in usuarios_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'password': make_password(user_data['password']),
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'company': empresa,
                'employee_id': user_data['employee_id'],
                'phone': user_data['phone'],
                'position': user_data['position'],
                'department': user_data['department'],
                'is_active': True
            }
        )
        if created:
            print(f"✅ Usuario '{user_data['username']}' creado")
        else:
            print(f"✅ Usuario '{user_data['username']}' ya existe")
    
    # 4. Crear entidades de demostración
    vehiculo_tipo = EntityType.objects.get(name='vehicle')
    empleado_tipo = EntityType.objects.get(name='employee')
    
    entidades_data = [
        {
            'entity_type': vehiculo_tipo,
            'external_id': 'VEH-SUST-001',
            'name': 'Vehículo Demo Sustentación',
            'metadata': {
                'brand': 'Toyota',
                'model': 'Corolla',
                'year': 2023,
                'plate': 'DEM-001',
                'color': 'Blanco'
            }
        },
        {
            'entity_type': vehiculo_tipo,
            'external_id': 'VEH-SUST-002',
            'name': 'Vehículo Demo 2',
            'metadata': {
                'brand': 'Ford',
                'model': 'Focus',
                'year': 2022,
                'plate': 'DEM-002',
                'color': 'Azul'
            }
        },
        {
            'entity_type': empleado_tipo,
            'external_id': 'EMP-SUST-001',
            'name': 'Juan Pérez Demo',
            'metadata': {
                'position': 'Desarrollador Senior',
                'department': 'IT',
                'hire_date': '2023-01-15',
                'salary': 5000000,
                'phone': '+57 300 444 4444'
            }
        }
    ]
    
    for entidad_data in entidades_data:
        entidad, created = Entity.objects.get_or_create(
            company=empresa,
            entity_type=entidad_data['entity_type'],
            external_id=entidad_data['external_id'],
            defaults={
                'name': entidad_data['name'],
                'metadata': entidad_data['metadata']
            }
        )
        if created:
            print(f"✅ Entidad '{entidad_data['name']}' creada")
        else:
            print(f"✅ Entidad '{entidad_data['name']}' ya existe")
    
    # 5. Mostrar resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE DATOS PREPARADOS")
    print("=" * 50)
    print(f"Empresa: {empresa.name} (ID: {empresa.id})")
    print(f"Usuarios: {User.objects.filter(company=empresa).count()}")
    print(f"Entidades: {Entity.objects.filter(company=empresa).count()}")
    print(f"Documentos: {Document.objects.filter(company=empresa).count()}")
    
    print("\n🔑 CREDENCIALES DE SUSTENTACIÓN:")
    print("-" * 30)
    for user_data in usuarios_data:
        print(f"Usuario: {user_data['username']}")
        print(f"Password: {user_data['password']}")
        print(f"Email: {user_data['email']}")
        print()
    
    print("📋 IDs IMPORTANTES PARA POSTMAN:")
    print("-" * 35)
    print(f"Company ID: {empresa.id}")
    print(f"Vehicle Entity ID: {Entity.objects.filter(company=empresa, entity_type=vehiculo_tipo).first().id}")
    print(f"Employee Entity ID: {Entity.objects.filter(company=empresa, entity_type=empleado_tipo).first().id}")
    print(f"Sustentador User ID: {User.objects.get(username='sustentador').id}")
    print(f"Aprobador1 User ID: {User.objects.get(username='aprobador1').id}")
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("-" * 20)
    print("1. Importar la colección de Postman")
    print("2. Importar las variables de entorno")
    print("3. Configurar las variables con los IDs mostrados arriba")
    print("4. Ejecutar el servidor: python manage.py runserver 8000")
    print("5. ¡Iniciar la sustentación!")
    
    return True

def main():
    """Función principal del script."""
    try:
        setup_django()
        success = preparar_datos_sustentacion()
        
        if success:
            print("\n🎉 ¡ENTORNO DE SUSTENTACIÓN LISTO!")
            print("El sistema está preparado para la sustentación.")
            return 0
        else:
            print("\n❌ Error preparando el entorno.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
