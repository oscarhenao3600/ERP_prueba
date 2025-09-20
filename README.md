# ERP Document Management System

## Descripción General

Este sistema es un módulo de gestión de documentos para un ERP (Sistema de Planificación de Recursos Empresariales) que permite:

- **Almacenar documentos** de manera segura en la nube (Amazon S3 o Google Cloud Storage)
- **Gestionar metadatos** de documentos en una base de datos PostgreSQL
- **Validar documentos** mediante un flujo jerárquico de aprobaciones
- **Controlar acceso** basado en empresas y entidades de negocio

### ¿Qué hace este sistema?

Imagina que trabajas en una empresa que necesita gestionar miles de documentos: fotos de vehículos, documentos de empleados, certificados fiscales, etc. Este sistema te permite:

1. **Subir documentos** de forma segura a la nube
2. **Organizar documentos** por empresa y tipo de entidad (vehículo, empleado, etc.)
3. **Crear flujos de aprobación** donde diferentes personas deben revisar y aprobar documentos
4. **Descargar documentos** cuando sea necesario
5. **Auditar** quién hizo qué y cuándo

### Características principales:

- **Seguridad**: Solo usuarios autorizados pueden acceder a documentos de su empresa
- **Escalabilidad**: Los archivos se almacenan en la nube, no en el servidor
- **Trazabilidad**: Se registra cada acción realizada
- **Flexibilidad**: Se puede configurar diferentes flujos de aprobación según el tipo de documento

## Arquitectura Técnica

El sistema está construido con Django (Python) y utiliza:

- **Base de datos**: PostgreSQL para metadatos
- **Almacenamiento**: Amazon S3 o Google Cloud Storage para archivos
- **API**: REST API con Django REST Framework
- **Autenticación**: Sistema de usuarios con permisos por empresa

## Estructura del Proyecto

```
erp_documents/
├── manage.py
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── README.md
├── erp_documents/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── documents/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services.py
│   ├── permissions.py
│   ├── urls.py
│   ├── admin.py
│   ├── migrations/
│   └── tests/
├── companies/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── migrations/
│   └── tests/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_services.py
    └── factories.py
```

## Instalación y Configuración

### Prerrequisitos

- Python 3.9+
- PostgreSQL 12+
- Docker (opcional)

### Instalación con Docker (Recomendado)

1. Clona el repositorio
2. Copia `.env.example` a `.env` y configura las variables
3. Ejecuta: `docker-compose up -d`
4. Ejecuta migraciones: `docker-compose exec web python manage.py migrate`
5. Crea superusuario: `docker-compose exec web python manage.py createsuperuser`

### Instalación Manual

1. Crea un entorno virtual: `python -m venv venv`
2. Activa el entorno: `source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows)
3. Instala dependencias: `pip install -r requirements.txt`
4. Configura PostgreSQL y crea la base de datos
5. Copia `.env.example` a `.env` y configura las variables
6. Ejecuta migraciones: `python manage.py migrate`
7. Crea superusuario: `python manage.py createsuperuser`
8. Ejecuta el servidor: `python manage.py runserver`

## Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/erp_documents

# Cloud Storage (S3)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=your_bucket.s3.amazonaws.com

# Configuración de URLs pre-firmadas
PRESIGNED_URL_EXPIRATION=3600  # 1 hora en segundos

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## API Endpoints

### 1. Cargar Documento
```http
POST /api/documents/
Content-Type: application/json

{
  "company_id": "uuid-company",
  "entity": {
    "entity_type": "vehicle",
    "entity_id": "uuid-veh"
  },
  "document": {
    "name": "soat.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 123456,
    "bucket_key": "companies/uuid-company/vehicles/uuid-veh/docs/soat-2025.pdf"
  },
  "validation_flow": {
    "enabled": true,
    "steps": [
      {
        "order": 1,
        "approver_user_id": "uuid-sebastian"
      },
      {
        "order": 2,
        "approver_user_id": "uuid-camilo"
      },
      {
        "order": 3,
        "approver_user_id": "uuid-juan"
      }
    ]
  }
}
```

### 2. Descargar Documento
```http
GET /api/documents/{document_id}/download
```

### 3. Aprobar Documento
```http
POST /api/documents/{document_id}/approve
Content-Type: application/json

{
  "actor_user_id": "uuid-juan",
  "reason": "Cumple requisitos."
}
```

### 4. Rechazar Documento
```http
POST /api/documents/{document_id}/reject
Content-Type: application/json

{
  "actor_user_id": "uuid-camilo",
  "reason": "Documento ilegible."
}
```

## Ejemplos de Pruebas con Postman

### Colección de Postman

Importa la colección `ERP_Documents.postman_collection.json` en Postman para tener todos los endpoints configurados.

### Ejemplo de Flujo Completo

1. **Crear Empresa**: POST `/api/companies/`
2. **Crear Usuario**: POST `/api/users/`
3. **Subir Documento**: POST `/api/documents/`
4. **Aprobar Documento**: POST `/api/documents/{id}/approve`
5. **Descargar Documento**: GET `/api/documents/{id}/download`

## Pruebas

### Ejecutar Pruebas Unitarias
```bash
python manage.py test
```

### Ejecutar con Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Pruebas de Integración
```bash
pytest tests/ -v
```

## Reglas de Negocio

### Estados de Validación
- **NULL**: Sin validación requerida
- **P**: Pendiente de aprobación
- **A**: Aprobado
- **R**: Rechazado (terminal)

### Jerarquía de Aprobación
- Los pasos tienen un orden numérico
- Un aprobador de mayor jerarquía (orden más alto) puede aprobar pasos previos automáticamente
- Un rechazo por cualquier aprobador marca el documento como rechazado inmediatamente

### Seguridad
- Solo usuarios con acceso a la empresa pueden operar con documentos
- Todas las acciones se registran con el usuario que las realizó
- Las URLs pre-firmadas tienen tiempo de expiración

## Monitoreo y Logs

El sistema registra:
- Creación y actualización de documentos
- Acciones de aprobación/rechazo
- Errores de acceso a cloud storage
- Intentos de acceso no autorizados

## Despliegue en Producción

1. Configura variables de entorno de producción
2. Usa un servidor WSGI como Gunicorn
3. Configura un proxy reverso (Nginx)
4. Usa HTTPS para todas las comunicaciones
5. Configura backups automáticos de la base de datos
6. Monitorea el uso de cloud storage

## Soporte y Contribución

Para reportar bugs o solicitar nuevas funcionalidades, crea un issue en el repositorio.

Para contribuir:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa los cambios con pruebas
4. Envía un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT.
