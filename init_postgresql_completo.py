#!/usr/bin/env python
"""
Script de inicialización completa para PostgreSQL - Sistema ERP de gestión de documentos.
Este script configura todo el sistema para demostración y sustentación.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_documents.settings.development')

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.db import transaction
from companies.models import Company, Entity
from documents.models import Document, ValidationFlow, ValidationStep
from documents.services_test import storage_service
import uuid
from datetime import datetime, timedelta

User = get_user_model()

def crear_directorios():
    """Crear directorios necesarios para el sistema."""
    print("📁 Creando directorios necesarios...")
    
    directorios = [
        'logs',
        'staticfiles',
        'media',
        's3_simulation',
        's3_simulation/companies',
        's3_simulation/companies/fb36990a-7101-4f07-9b1f-c58bf492355b',
        's3_simulation/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles',
        's3_simulation/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/employees',
        's3_simulation/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/equipment',
        's3_simulation/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/facilities'
    ]
    
    for directorio in directorios:
        Path(directorio).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directorio}")

def ejecutar_migraciones():
    """Ejecutar migraciones de Django."""
    print("🔄 Ejecutando migraciones...")
    
    try:
        # Crear migraciones si no existen
        execute_from_command_line(['manage.py', 'makemigrations'])
        # Ejecutar migraciones
        execute_from_command_line(['manage.py', 'migrate'])
        print("   ✅ Migraciones ejecutadas correctamente")
    except Exception as e:
        print(f"   ❌ Error en migraciones: {e}")
        return False
    
    return True

def crear_usuarios(company):
    """Crear usuarios del sistema."""
    print("👥 Creando usuarios del sistema...")
    
    usuarios_data = [
        {
            'username': 'sustentador',
            'email': 'sustentador@demo.com',
            'first_name': 'Usuario',
            'last_name': 'Sustentador',
            'password': 'sustentacion123',
            'company': company,
            'is_staff': True,
            'is_active': True
        },
        {
            'username': 'aprobador1',
            'email': 'aprobador1@demo.com',
            'first_name': 'Supervisor',
            'last_name': 'Aprobador',
            'password': 'aprobador123',
            'company': company,
            'is_staff': True,
            'is_active': True
        },
        {
            'username': 'aprobador2',
            'email': 'aprobador2@demo.com',
            'first_name': 'Gerente',
            'last_name': 'Aprobador',
            'password': 'aprobador123',
            'company': company,
            'is_staff': True,
            'is_active': True
        },
        {
            'username': 'admin',
            'email': 'admin@demo.com',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'password': 'admin123',
            'company': company,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    ]
    
    usuarios_creados = {}
    
    for user_data in usuarios_data:
        username = user_data['username']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(**user_data)
            usuarios_creados[username] = user
            print(f"   ✅ Usuario creado: {username}")
        else:
            usuarios_creados[username] = User.objects.get(username=username)
            print(f"   ℹ️  Usuario existente: {username}")
    
    return usuarios_creados

def crear_empresa():
    """Crear empresa demo."""
    print("🏢 Creando empresa demo...")
    
    company_id = 'fb36990a-7101-4f07-9b1f-c58bf492355b'
    
    if not Company.objects.filter(id=company_id).exists():
        company = Company.objects.create(
            id=company_id,
            name='Empresa Sustentación Demo',
            legal_name='Empresa Sustentación Demo S.A.S.',
            address='Calle Demo 123, Ciudad Demo',
            phone='+1-555-0123',
            email='info@empresa-demo.com',
            tax_id='123456789',
            is_active=True
        )
        print(f"   ✅ Empresa creada: {company.name}")
    else:
        company = Company.objects.get(id=company_id)
        print(f"   ℹ️  Empresa existente: {company.name}")
    
    return company

def crear_tipos_entidad():
    """Crear tipos de entidad."""
    print("📋 Creando tipos de entidad...")
    
    from companies.models import EntityType
    
    tipos_data = [
        {
            'id': '01c22aa0-3eb2-38d2-81b1-085c78b65a6a',
            'name': 'vehicle',
            'display_name': 'Vehículo',
            'description': 'Vehículos de la empresa',
            'is_active': True
        },
        {
            'id': '02d33bb1-4fc3-49e3-91b2-196d89c76b7b',
            'name': 'employee',
            'display_name': 'Empleado',
            'description': 'Empleados de la empresa',
            'is_active': True
        },
        {
            'id': '03e44cc2-5fd4-5af4-a2c3-2a7e9ad87c8c',
            'name': 'equipment',
            'display_name': 'Equipo',
            'description': 'Equipos y herramientas',
            'is_active': True
        }
    ]
    
    tipos_creados = {}
    
    for tipo_data in tipos_data:
        tipo_name = tipo_data['name']
        if not EntityType.objects.filter(name=tipo_name).exists():
            tipo = EntityType.objects.create(**tipo_data)
            tipos_creados[tipo_name] = tipo
            print(f"   ✅ Tipo creado: {tipo.display_name}")
        else:
            tipo = EntityType.objects.get(name=tipo_name)
            tipos_creados[tipo_name] = tipo
            print(f"   ℹ️  Tipo existente: {tipo.display_name}")
    
    return tipos_creados

def crear_entidades(company, usuarios, tipos_entidad):
    """Crear entidades demo."""
    print("🚗 Creando entidades demo...")
    
    entidades_data = [
        {
            'id': '02d33ab1-4fc3-49e3-91b2-196d89c76b7b',
            'entity_type': 'vehicle',
            'external_id': 'VEH-DEMO-001',
            'name': 'Vehículo Demo',
            'metadata': {
                'brand': 'Toyota',
                'model': 'Yaris',
                'year': 2024,
                'plate': 'DEMO-001',
                'color': 'Rojo',
                'engine': '1.5L',
                'fuel_type': 'Gasolina',
                'vin': '1HGBH41JXMN109186',
                'insurance_number': 'INS-001-2024',
                'registration_date': '2024-01-15'
            }
        },
        {
            'id': '648eda80-bf9d-408d-92c4-089c6ab821b7',
            'entity_type': 'employee',
            'external_id': 'EMP-DEMO-001',
            'name': 'Empleado Demo',
            'metadata': {
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'email': 'juan.perez@demo.com',
                'position': 'Desarrollador',
                'department': 'IT',
                'hire_date': '2024-01-15',
                'salary': 50000,
                'employee_id': 'EMP-001',
                'phone': '+1-555-0124',
                'address': 'Calle Empleado 456, Ciudad Demo'
            }
        },
        {
            'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            'entity_type': 'equipment',
            'external_id': 'EQP-DEMO-001',
            'name': 'Equipo Demo',
            'metadata': {
                'type': 'Laptop',
                'brand': 'Dell',
                'model': 'Latitude 5520',
                'serial_number': 'DL-001-2024',
                'purchase_date': '2024-01-10',
                'warranty_expiry': '2025-01-10',
                'assigned_to': 'juan.perez@demo.com',
                'status': 'active'
            }
        }
    ]
    
    entidades_creadas = {}
    
    for entidad_data in entidades_data:
        entity_id = entidad_data['id']
        if not Entity.objects.filter(id=entity_id).exists():
            entidad = Entity.objects.create(
                id=entity_id,
                company=company,
                entity_type=tipos_entidad[entidad_data['entity_type']],
                external_id=entidad_data['external_id'],
                name=entidad_data['name'],
                metadata=entidad_data['metadata'],
                is_active=True
            )
            entidades_creadas[entidad_data['entity_type'].name] = entidad
            print(f"   ✅ Entidad creada: {entidad.name} ({entidad.entity_type})")
        else:
            entidad = Entity.objects.get(id=entity_id)
            entidades_creadas[entidad.entity_type.name] = entidad
            print(f"   ℹ️  Entidad existente: {entidad.name} ({entidad.entity_type})")
    
    return entidades_creadas

def crear_tags():
    """Crear tags para documentos."""
    print("🏷️  Creando tags de documentos...")
    
    tags_data = [
        'demo', 'soat', 'vehiculo', 'seguro', 'contrato', 'empleado', 
        'laboral', 'equipo', 'mantenimiento', 'factura', 'recibo', 
        'certificado', 'licencia', 'permiso', 'manual', 'procedimiento'
    ]
    
    print(f"   ✅ Tags disponibles: {', '.join(tags_data)}")
    
    return tags_data

def crear_documentos(company, entidades, usuarios, tags):
    """Crear documentos demo."""
    print("📄 Creando documentos demo...")
    print(f"   🔍 Entidades disponibles: {list(entidades.keys())}")
    
    documentos_data = [
        {
            'id': '05a7bcab-9015-4923-9bd3-ed54424d6fc7',
            'name': 'SOAT Vehículo Demo.pdf',
            'mime_type': 'application/pdf',
            'size_bytes': 245760,
            'bucket_key': 'companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles/02d33ab1-4fc3-49e3-91b2-196d89c76b7b/docs/soat-demo.pdf',
            'file_hash': 'sha256:demo123456789',
            'description': 'SOAT del vehículo demo para prueba del sistema',
            'tags': ['soat', 'vehiculo', 'seguro', 'demo'],
            'entity_type': 'vehicle',
            'validation_steps': [
                {'approver': 'sustentador', 'comments': 'Revisión inicial del documento'},
                {'approver': 'aprobador1', 'comments': 'Aprobación del supervisor'},
                {'approver': 'aprobador2', 'comments': 'Aprobación final del gerente'}
            ]
        },
        {
            'id': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
            'name': 'Contrato Laboral Empleado.pdf',
            'mime_type': 'application/pdf',
            'size_bytes': 512000,
            'bucket_key': 'companies/fb36990a-7101-4f07-9b1f-c58bf492355b/employees/648eda80-bf9d-408d-92c4-089c6ab821b7/docs/contrato-laboral.pdf',
            'file_hash': 'sha256:contrato123456789',
            'description': 'Contrato laboral del empleado demo',
            'tags': ['contrato', 'empleado', 'laboral', 'demo'],
            'entity_type': 'employee',
            'validation_steps': [
                {'approver': 'sustentador', 'comments': 'Revisión del contrato'},
                {'approver': 'aprobador1', 'comments': 'Aprobación de RRHH'}
            ]
        },
        {
            'id': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
            'name': 'Manual de Equipo.pdf',
            'mime_type': 'application/pdf',
            'size_bytes': 1024000,
            'bucket_key': 'companies/fb36990a-7101-4f07-9b1f-c58bf492355b/equipment/a1b2c3d4-e5f6-7890-abcd-ef1234567890/docs/manual-equipo.pdf',
            'file_hash': 'sha256:manual123456789',
            'description': 'Manual de usuario del equipo demo',
            'tags': ['manual', 'equipo', 'procedimiento', 'demo'],
            'entity_type': 'equipment',
            'validation_steps': [
                {'approver': 'sustentador', 'comments': 'Revisión del manual'},
                {'approver': 'aprobador1', 'comments': 'Aprobación técnica'}
            ]
        }
    ]
    
    documentos_creados = {}
    
    for doc_data in documentos_data:
        doc_id = doc_data['id']
        if not Document.objects.filter(id=doc_id).exists():
            # Crear documento
            documento = Document.objects.create(
                id=doc_id,
                company=company,
                entity=entidades[doc_data['entity_type']],
                name=doc_data['name'],
                mime_type=doc_data['mime_type'],
                size_bytes=doc_data['size_bytes'],
                bucket_key=doc_data['bucket_key'],
                file_hash=doc_data['file_hash'],
                description=doc_data['description'],
                tags=doc_data['tags'],  # Usar el campo tags directamente
                validation_status='P',  # Pendiente
                created_by=usuarios['sustentador']
            )
            
            # Crear flujo de validación
            flow = ValidationFlow.objects.create(
                document=documento,
                is_active=True
            )
            
            # Crear pasos de validación
            for i, step_data in enumerate(doc_data['validation_steps'], 1):
                approver_username = step_data['approver']
                if approver_username in usuarios:
                    ValidationStep.objects.create(
                        validation_flow=flow,
                        order=i,
                        approver=usuarios[approver_username],
                        status='P'  # Pendiente
                    )
            
            documentos_creados[doc_data['entity_type']] = documento
            print(f"   ✅ Documento creado: {documento.name}")
        else:
            documento = Document.objects.get(id=doc_id)
            documentos_creados[doc_data['entity_type']] = documento
            print(f"   ℹ️  Documento existente: {documento.name}")
    
    return documentos_creados

def simular_archivos(documentos):
    """Simular archivos en el almacenamiento."""
    print("💾 Simulando archivos en almacenamiento...")
    
    for entity_type, documento in documentos.items():
        # Crear archivo simulado
        file_data = b'%PDF-1.4\n%Demo PDF Content\n' + b'Demo content for ' + documento.name.encode() + b'\n' * 1000
        
        # Almacenar en el servicio simulado
        result = storage_service.store_file(
            documento.bucket_key,
            {
                'size': documento.size_bytes,
                'mime_type': documento.mime_type,
                'name': documento.name,
                'created_at': datetime.now().isoformat(),
                'content': file_data  # Agregar el contenido del archivo
            }
        )
        
        if result:
            print(f"   ✅ Archivo simulado: {documento.name}")
        else:
            print(f"   ❌ Error simulando archivo: {documento.name}")

def mostrar_resumen(usuarios, company, entidades, documentos):
    """Mostrar resumen del sistema inicializado."""
    print("\n" + "="*80)
    print("🎉 SISTEMA ERP DE GESTIÓN DE DOCUMENTOS INICIALIZADO")
    print("="*80)
    
    print(f"\n🏢 EMPRESA:")
    print(f"   ID: {company.id}")
    print(f"   Nombre: {company.name}")
    print(f"   Email: {company.email}")
    
    print(f"\n👥 USUARIOS:")
    for username, user in usuarios.items():
        print(f"   {username}: {user.email} (ID: {user.id})")
    
    print(f"\n🚗 ENTIDADES:")
    for entity_type, entidad in entidades.items():
        print(f"   {entity_type}: {entidad.name} (ID: {entidad.id})")
    
    print(f"\n📄 DOCUMENTOS:")
    for entity_type, documento in documentos.items():
        print(f"   {entity_type}: {documento.name} (ID: {documento.id})")
    
    print(f"\n🔑 CREDENCIALES DE ACCESO:")
    print(f"   Sustentador: sustentador / sustentacion123")
    print(f"   Aprobador 1: aprobador1 / aprobador123")
    print(f"   Aprobador 2: aprobador2 / aprobador123")
    print(f"   Admin: admin / admin123")
    
    print(f"\n🌐 ENDPOINTS PRINCIPALES:")
    print(f"   API Base: http://localhost:8000/api/")
    print(f"   Login: http://localhost:8000/api/auth/login/")
    print(f"   Documentos: http://localhost:8000/api/documents/")
    print(f"   Empresas: http://localhost:8000/api/companies/")
    print(f"   Entidades: http://localhost:8000/api/entities/")
    
    print(f"\n📊 ESTADÍSTICAS:")
    # Estadísticas de almacenamiento
    print(f"   Archivos simulados: {len(documentos)}")
    print(f"   Tamaño total: {sum(doc.size_bytes for doc in documentos.values())} bytes")
    print(f"   Tipos MIME: {len(set(doc.mime_type for doc in documentos.values()))}")
    
    print(f"\n🚀 PRÓXIMOS PASOS:")
    print(f"   1. Iniciar servidor: python manage.py runserver 8000")
    print(f"   2. Importar colección Postman: ERP_Documents_PostgreSQL.postman_collection.json")
    print(f"   3. Importar entorno Postman: ERP_Documents_PostgreSQL.postman_environment.json")
    print(f"   4. Ejecutar flujo de prueba desde Postman")
    
    print("\n" + "="*80)

def main():
    """Función principal de inicialización."""
    print("🚀 INICIANDO CONFIGURACIÓN COMPLETA DEL SISTEMA ERP (PostgreSQL)")
    print("="*80)
    
    try:
        # 1. Crear directorios
        crear_directorios()
        
        # 2. Ejecutar migraciones
        if not ejecutar_migraciones():
            print("❌ Error en migraciones. Abortando...")
            return False
        
        # 3. Crear empresa
        company = crear_empresa()
        
        # 4. Crear usuarios
        usuarios = crear_usuarios(company)
        
        # 5. Crear tipos de entidad
        tipos_entidad = crear_tipos_entidad()
        
        # 6. Crear entidades
        entidades = crear_entidades(company, usuarios, tipos_entidad)
        
        # 7. Crear tags
        tags = crear_tags()
        
        # 8. Crear documentos
        documentos = crear_documentos(company, entidades, usuarios, tags)
        
        # 9. Simular archivos
        simular_archivos(documentos)
        
        # 10. Mostrar resumen
        mostrar_resumen(usuarios, company, entidades, documentos)
        
        print("\n✅ SISTEMA INICIALIZADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA INICIALIZACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
