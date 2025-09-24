@echo off
echo 🚀 CONFIGURACIÓN RÁPIDA CON SQLITE
echo ===================================

echo 📁 Creando directorios...
if not exist logs mkdir logs
if not exist staticfiles mkdir staticfiles
if not exist media mkdir media
if not exist s3_simulation mkdir s3_simulation

echo 🔄 Ejecutando migraciones...
python manage.py makemigrations
python manage.py migrate

echo 👤 Creando superusuario...
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul || echo ℹ️  Superusuario ya existe

echo 🔑 Estableciendo contraseña del admin...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='admin'); user.set_password('admin123'); user.save()"

echo 👥 Creando usuarios de demo...
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# Crear sustentador
user1, created = User.objects.get_or_create(
    username='sustentador',
    defaults={
        'email': 'sustentador@demo.com',
        'first_name': 'Usuario',
        'last_name': 'Sustentador',
        'is_staff': True,
        'is_active': True
    }
)
if created:
    user1.set_password('sustentacion123')
    user1.save()
    print('✅ Usuario sustentador creado')

# Crear aprobador1
user2, created = User.objects.get_or_create(
    username='aprobador1',
    defaults={
        'email': 'aprobador1@demo.com',
        'first_name': 'Supervisor',
        'last_name': 'Aprobador',
        'is_staff': True,
        'is_active': True
    }
)
if created:
    user2.set_password('aprobador123')
    user2.save()
    print('✅ Usuario aprobador1 creado')

# Crear aprobador2
user3, created = User.objects.get_or_create(
    username='aprobador2',
    defaults={
        'email': 'aprobador2@demo.com',
        'first_name': 'Gerente',
        'last_name': 'Aprobador',
        'is_staff': True,
        'is_active': True
    }
)
if created:
    user3.set_password('aprobador123')
    user3.save()
    print('✅ Usuario aprobador2 creado')
"

echo 🏢 Creando empresa demo...
python manage.py shell -c "
from companies.models import Company
company, created = Company.objects.get_or_create(
    id='fb36990a-7101-4f07-9b1f-c58bf492355b',
    defaults={
        'name': 'Empresa Sustentación Demo',
        'description': 'Empresa de demostración para el sistema ERP',
        'address': 'Calle Demo 123, Ciudad Demo',
        'phone': '+1-555-0123',
        'email': 'info@empresa-demo.com',
        'website': 'https://www.empresa-demo.com',
        'tax_id': '123456789',
        'is_active': True
    }
)
if created:
    print('✅ Empresa creada')
else:
    print('ℹ️  Empresa ya existe')
"

echo 🚗 Creando entidades demo...
python manage.py shell -c "
from companies.models import Company, Entity
company = Company.objects.get(id='fb36990a-7101-4f07-9b1f-c58bf492355b')

# Crear vehículo
vehicle, created = Entity.objects.get_or_create(
    id='02d33ab1-4fc3-49e3-91b2-196d89c76b7b',
    defaults={
        'company': company,
        'entity_type': 'vehicle',
        'external_id': 'VEH-DEMO-001',
        'name': 'Vehículo Demo',
        'metadata': {
            'brand': 'Toyota',
            'model': 'Yaris',
            'year': 2024,
            'plate': 'DEMO-001',
            'color': 'Rojo'
        },
        'is_active': True
    }
)
if created:
    print('✅ Vehículo creado')
else:
    print('ℹ️  Vehículo ya existe')

# Crear empleado
employee, created = Entity.objects.get_or_create(
    id='648eda80-bf9d-408d-92c4-089c6ab821b7',
    defaults={
        'company': company,
        'entity_type': 'employee',
        'external_id': 'EMP-DEMO-001',
        'name': 'Empleado Demo',
        'metadata': {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan.perez@demo.com',
            'position': 'Desarrollador',
            'department': 'IT'
        },
        'is_active': True
    }
)
if created:
    print('✅ Empleado creado')
else:
    print('ℹ️  Empleado ya existe')
"

echo 📄 Creando documento demo...
python manage.py shell -c "
from companies.models import Company, Entity
from documents.models import Document, ValidationFlow, ValidationStep
from django.contrib.auth import get_user_model

User = get_user_model()
company = Company.objects.get(id='fb36990a-7101-4f07-9b1f-c58bf492355b')
vehicle = Entity.objects.get(id='02d33ab1-4fc3-49e3-91b2-196d89c76b7b')
sustentador = User.objects.get(username='sustentador')
aprobador1 = User.objects.get(username='aprobador1')
aprobador2 = User.objects.get(username='aprobador2')

# Crear documento
documento, created = Document.objects.get_or_create(
    id='05a7bcab-9015-4923-9bd3-ed54424d6fc7',
    defaults={
        'company': company,
        'entity': vehicle,
        'name': 'SOAT Vehículo Demo.pdf',
        'mime_type': 'application/pdf',
        'size_bytes': 245760,
        'bucket_key': 'companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles/02d33ab1-4fc3-49e3-91b2-196d89c76b7b/docs/soat-demo.pdf',
        'file_hash': 'sha256:demo123456789',
        'description': 'SOAT del vehículo demo para prueba del sistema',
        'validation_status': 'P',
        'created_by': sustentador
    }
)

if created:
    # Crear flujo de validación
    flow = ValidationFlow.objects.create(
        document=documento,
        is_active=True,
        description='Flujo de validación para SOAT'
    )
    
    # Crear pasos de validación
    ValidationStep.objects.create(
        validation_flow=flow,
        order=1,
        approver=sustentador,
        status='P',
        comments='Revisión inicial del documento'
    )
    
    ValidationStep.objects.create(
        validation_flow=flow,
        order=2,
        approver=aprobador1,
        status='P',
        comments='Aprobación del supervisor'
    )
    
    ValidationStep.objects.create(
        validation_flow=flow,
        order=3,
        approver=aprobador2,
        status='P',
        comments='Aprobación final del gerente'
    )
    
    print('✅ Documento creado con flujo de validación')
else:
    print('ℹ️  Documento ya existe')
"

echo 💾 Simulando archivo...
python manage.py shell -c "
from documents.models import Document
from documents.services_test import storage_service

documento = Document.objects.get(id='05a7bcab-9015-4923-9bd3-ed54424d6fc7')

# Crear archivo simulado
file_data = b'%PDF-1.4\n%Demo PDF Content\n' + b'Demo content for ' + documento.name.encode() + b'\n' * 1000

# Almacenar en el servicio simulado
result = storage_service.store_file(
    documento.bucket_key,
    file_data,
    {
        'size': documento.size_bytes,
        'mime_type': documento.mime_type,
        'name': documento.name
    }
)

if result['success']:
    print('✅ Archivo simulado')
else:
    print('❌ Error simulando archivo')
"

echo ✅ CONFIGURACIÓN COMPLETADA
echo ===================================
echo 🎉 El sistema ERP está listo para usar.
echo.
echo 🔑 CREDENCIALES:
echo    Admin: admin / admin123
echo    Sustentador: sustentador / sustentacion123
echo    Aprobador 1: aprobador1 / aprobador123
echo    Aprobador 2: aprobador2 / aprobador123
echo.
echo 🚀 PRÓXIMOS PASOS:
echo    1. python manage.py runserver 8000
echo    2. Abrir http://localhost:8000
echo    3. Usar Postman para probar la API
echo.
echo 📊 DATOS CREADOS:
echo    - Empresa: Empresa Sustentación Demo
echo    - Vehículo: Vehículo Demo (Toyota Yaris)
echo    - Empleado: Empleado Demo (Juan Pérez)
echo    - Documento: SOAT Vehículo Demo.pdf
echo.
pause

