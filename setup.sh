#!/bin/bash
# Script de inicialización para el sistema ERP de gestión de documentos

echo "🚀 Iniciando configuración del sistema ERP de gestión de documentos..."

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instala Python 3.9 o superior."
    exit 1
fi

# Verificar que pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado. Por favor instala pip3."
    exit 1
fi

# Crear directorio de logs
echo "📁 Creando directorio de logs..."
mkdir -p logs

# Crear directorio de media
echo "📁 Creando directorio de media..."
mkdir -p media

# Crear directorio de static
echo "📁 Creando directorio de static..."
mkdir -p static

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cp env_example.txt .env
    echo "⚠️  Por favor configura las variables en el archivo .env antes de continuar."
    echo "   Especialmente las credenciales de AWS S3 y la configuración de la base de datos."
    read -p "¿Has configurado el archivo .env? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Por favor configura el archivo .env y ejecuta este script nuevamente."
        exit 1
    fi
fi

# Instalar dependencias
echo "📦 Instalando dependencias de Python..."
pip3 install -r requirements.txt

# Verificar que PostgreSQL está disponible
echo "🗄️  Verificando conexión a PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL no está instalado. Por favor instala PostgreSQL 12 o superior."
    echo "   En Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "   En macOS: brew install postgresql"
    echo "   En Windows: Descarga desde https://www.postgresql.org/download/"
fi

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones de Django..."
python3 manage.py makemigrations
python3 manage.py migrate

# Crear superusuario
echo "👤 Creando superusuario..."
python3 manage.py createsuperuser --noinput --username admin --email admin@example.com || echo "⚠️  Superusuario ya existe o hubo un error."

# Crear datos de prueba
echo "🧪 Creando datos de prueba..."
python3 manage.py shell << EOF
from companies.models import Company, EntityType, Entity, User
from documents.models import Document, ValidationFlow, ValidationStep
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

print(f"✅ Datos de prueba creados:")
print(f"   - Empresa: {company.name}")
print(f"   - Usuario: {user1.username} (contraseña: demo123)")
print(f"   - Aprobador: {approver.username} (contraseña: demo123)")
print(f"   - Vehículo: {vehicle.name}")
print(f"   - Empleado: {employee.name}")
EOF

# Ejecutar pruebas
echo "🧪 Ejecutando pruebas unitarias..."
python3 manage.py test

# Generar reporte de coverage
echo "📊 Generando reporte de coverage..."
coverage run --source='.' manage.py test
coverage report
coverage html

echo "✅ Configuración completada exitosamente!"
echo ""
echo "🎉 El sistema ERP de gestión de documentos está listo para usar."
echo ""
echo "📋 Próximos pasos:"
echo "   1. Configura las credenciales de AWS S3 en el archivo .env"
echo "   2. Ejecuta: python3 manage.py runserver"
echo "   3. Accede a: http://localhost:8000/admin/"
echo "   4. Usa las credenciales: admin/admin (o las que configuraste)"
echo "   5. Importa la colección de Postman para probar la API"
echo ""
echo "📚 Documentación:"
echo "   - README.md: Documentación general del sistema"
echo "   - GUIA_PRUEBAS_POSTMAN.md: Guía de pruebas con Postman"
echo "   - ERP_Documents.postman_collection.json: Colección de Postman"
echo ""
echo "🔧 Comandos útiles:"
echo "   - python3 manage.py runserver: Iniciar servidor de desarrollo"
echo "   - python3 manage.py test: Ejecutar pruebas"
echo "   - python3 manage.py shell: Abrir shell de Django"
echo "   - python3 manage.py createsuperuser: Crear superusuario"
echo ""
echo "¡Disfruta usando el sistema! 🚀"
