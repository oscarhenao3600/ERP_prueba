# 📁 ESTRUCTURA DEL PROYECTO - ERP DOCUMENTS

```
ERP_Prueba/
├── 📁 companies/                    # App de empresas y usuarios
│   ├── models.py                    # Modelos: Company, User, Entity, EntityType
│   ├── views.py                     # ViewSets para API REST
│   ├── serializers.py               # Serializers para JSON
│   ├── admin.py                     # Configuración del admin
│   ├── urls.py                      # URLs de la app
│   └── migrations/                  # Migraciones de BD
│       └── 0001_initial.py
│
├── 📁 documents/                    # App principal de documentos
│   ├── models.py                    # Modelos: Document, ValidationFlow, etc.
│   ├── views.py                     # API endpoints principales
│   ├── serializers.py               # Serializers de documentos
│   ├── services.py                  # Servicios S3/GCS
│   ├── services_test.py             # Mock service para pruebas
│   ├── validation_service.py        # Lógica de validación jerárquica
│   ├── admin.py                     # Admin de documentos
│   ├── urls.py                      # URLs de documentos
│   └── migrations/                  # Migraciones de documentos
│       └── 0001_initial.py
│
├── 📁 erp_documents/                # Configuración principal
│   ├── settings/                    # Configuraciones por entorno
│   │   ├── base.py                  # Configuración base
│   │   ├── development.py           # Desarrollo (SQLite)
│   │   └── production.py            # Producción (PostgreSQL)
│   ├── urls.py                      # URLs principales
│   ├── wsgi.py                      # WSGI para deployment
│   └── db.sqlite3                   # Base de datos SQLite
│
├── 📁 tests/                        # Pruebas unitarias
│   ├── test_models.py               # Pruebas de modelos
│   ├── test_services_simple.py      # Pruebas de servicios
│   ├── test_views.py                # Pruebas de vistas
│   └── test_cases_uso.py            # Casos de uso específicos
│
├── 📄 requirements.txt              # Dependencias Python
├── 📄 manage.py                     # Script de gestión Django
├── 📄 README.md                     # Documentación principal
├── 📄 .env.example                  # Variables de entorno
├── 📄 docker-compose.yml            # Configuración Docker
├── 📄 Dockerfile                    # Imagen Docker
└── 📄 ERP_Documents.postman_collection.json  # Colección Postman
```

## 🛠️ STACK TECNOLÓGICO

### Backend
- **Django 4.2.7** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL** - Base de datos (SQLite para desarrollo)
- **boto3** - Cliente AWS S3
- **python-decouple** - Gestión de variables de entorno

### Testing
- **pytest** - Framework de pruebas
- **pytest-django** - Integración con Django
- **model_bakery** - Generación de datos de prueba

### Deployment
- **Docker** - Containerización
- **Docker Compose** - Orquestación
- **nginx** - Servidor web (producción)

## 📋 APPS DEL PROYECTO

### 1. **companies**
- Gestión de empresas
- Usuarios del sistema
- Entidades de negocio (vehículos, empleados)
- Tipos de entidad

### 2. **documents**
- Gestión de documentos
- Flujos de validación
- Servicios de cloud storage
- API endpoints principales

## 🔧 ARCHIVOS DE CONFIGURACIÓN

- `settings/base.py` - Configuración común
- `settings/development.py` - Desarrollo local
- `settings/production.py` - Producción
- `requirements.txt` - Dependencias
- `.env.example` - Variables de entorno
