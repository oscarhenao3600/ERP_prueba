@echo off
REM Script de inicialización para el sistema ERP de gestión de documentos (Windows)

echo 🚀 Iniciando configuración del sistema ERP de gestión de documentos...

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado. Por favor instala Python 3.9 o superior.
    echo    Descarga desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar que pip está instalado
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip no está instalado. Por favor instala pip.
    pause
    exit /b 1
)

REM Crear directorio de logs
echo 📁 Creando directorio de logs...
if not exist logs mkdir logs

REM Crear directorio de media
echo 📁 Creando directorio de media...
if not exist media mkdir media

REM Crear directorio de static
echo 📁 Creando directorio de static...
if not exist static mkdir static

REM Crear archivo .env si no existe
if not exist .env (
    echo 📝 Creando archivo .env...
    copy env_example.txt .env
    echo ⚠️  Por favor configura las variables en el archivo .env antes de continuar.
    echo    Especialmente las credenciales de AWS S3 y la configuración de la base de datos.
    set /p response="¿Has configurado el archivo .env? (y/n): "
    if /i not "%response%"=="y" (
        echo ❌ Por favor configura el archivo .env y ejecuta este script nuevamente.
        pause
        exit /b 1
    )
)

REM Instalar dependencias
echo 📦 Instalando dependencias de Python...
pip install -r requirements.txt

REM Verificar que PostgreSQL está disponible
echo 🗄️  Verificando conexión a PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL no está instalado. Por favor instala PostgreSQL 12 o superior.
    echo    Descarga desde: https://www.postgresql.org/download/windows/
)

REM Ejecutar migraciones
echo 🔄 Ejecutando migraciones de Django...
python manage.py makemigrations
python manage.py migrate

REM Crear superusuario
echo 👤 Creando superusuario...
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul || echo ⚠️  Superusuario ya existe o hubo un error.

REM Crear datos de prueba
echo 🧪 Creando datos de prueba...
python manage.py shell -c "
from companies.models import Company, EntityType, Entity, User
import uuid

# Crear empresa de prueba
company, created = Company.objects.get_or_create(
    tax_id='900123456-1',
    defaults={
        'name': 'Empresa Demo',
        'legal_name': 'Empresa Demo S.A.S.',
        'email': 'demo@empresa.com',
        'is_active': True
    }
)

# Crear tipos de entidad
vehicle_type, created = EntityType.objects.get_or_create(
    name='vehicle',
    defaults={
        'display_name': 'Vehículo',
        'description': 'Tipo de entidad para vehículos',
        'is_active': True
    }
)

employee_type, created = EntityType.objects.get_or_create(
    name='employee',
    defaults={
        'display_name': 'Empleado',
        'description': 'Tipo de entidad para empleados',
        'is_active': True
    }
)

# Crear usuarios de prueba
user1, created = User.objects.get_or_create(
    username='demo_user',
    defaults={
        'email': 'demo@test.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'company': company,
        'employee_id': 'EMP001',
        'position': 'Analista',
        'department': 'TI',
        'is_active': True
    }
)
if created:
    user1.set_password('demo123')
    user1.save()

approver, created = User.objects.get_or_create(
    username='demo_approver',
    defaults={
        'email': 'approver@test.com',
        'first_name': 'Demo',
        'last_name': 'Approver',
        'company': company,
        'employee_id': 'EMP002',
        'position': 'Supervisor',
        'department': 'TI',
        'is_company_admin': True,
        'is_active': True
    }
)
if created:
    approver.set_password('demo123')
    approver.save()

# Crear entidades de prueba
vehicle, created = Entity.objects.get_or_create(
    company=company,
    entity_type=vehicle_type,
    external_id='VEH001',
    defaults={
        'name': 'Vehículo Demo',
        'metadata': {'brand': 'Toyota', 'model': 'Corolla', 'year': 2023},
        'is_active': True
    }
)

employee, created = Entity.objects.get_or_create(
    company=company,
    entity_type=employee_type,
    external_id='EMP001',
    defaults={
        'name': 'Empleado Demo',
        'metadata': {'position': 'Analista', 'department': 'TI'},
        'is_active': True
    }
)

print('✅ Datos de prueba creados:')
print(f'   - Empresa: {company.name}')
print(f'   - Usuario: {user1.username} (contraseña: demo123)')
print(f'   - Aprobador: {approver.username} (contraseña: demo123)')
print(f'   - Vehículo: {vehicle.name}')
print(f'   - Empleado: {employee.name}')
"

REM Ejecutar pruebas
echo 🧪 Ejecutando pruebas unitarias...
python manage.py test

REM Generar reporte de coverage
echo 📊 Generando reporte de coverage...
coverage run --source=. manage.py test
coverage report
coverage html

echo ✅ Configuración completada exitosamente!
echo.
echo 🎉 El sistema ERP de gestión de documentos está listo para usar.
echo.
echo 📋 Próximos pasos:
echo    1. Configura las credenciales de AWS S3 en el archivo .env
echo    2. Ejecuta: python manage.py runserver
echo    3. Accede a: http://localhost:8000/admin/
echo    4. Usa las credenciales: admin/admin (o las que configuraste)
echo    5. Importa la colección de Postman para probar la API
echo.
echo 📚 Documentación:
echo    - README.md: Documentación general del sistema
echo    - GUIA_PRUEBAS_POSTMAN.md: Guía de pruebas con Postman
echo    - ERP_Documents.postman_collection.json: Colección de Postman
echo.
echo 🔧 Comandos útiles:
echo    - python manage.py runserver: Iniciar servidor de desarrollo
echo    - python manage.py test: Ejecutar pruebas
echo    - python manage.py shell: Abrir shell de Django
echo    - python manage.py createsuperuser: Crear superusuario
echo.
echo ¡Disfruta usando el sistema! 🚀
pause
