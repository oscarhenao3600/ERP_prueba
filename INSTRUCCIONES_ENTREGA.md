# 📦 INSTRUCCIONES DE ENTREGA - Sistema ERP de Gestión de Documentos

## 🎯 Contenido del Paquete

Este paquete contiene un **sistema completo de gestión de documentos para ERP** desarrollado en Django con todas las funcionalidades solicitadas y valor agregado adicional.

## 📁 Estructura del Proyecto

```
ERP_Prueba/
├── 📋 DOCUMENTACIÓN
│   ├── README.md                          # Documentación principal
│   ├── RESUMEN_EJECUTIVO.md               # Resumen ejecutivo del proyecto
│   ├── GUIA_PRUEBAS_POSTMAN.md            # Guía de pruebas con Postman
│   └── ERP_Documents.postman_collection.json # Colección de Postman
│
├── ⚙️ CONFIGURACIÓN
│   ├── requirements.txt                   # Dependencias de Python
│   ├── docker-compose.yml                # Configuración de Docker
│   ├── Dockerfile                        # Imagen de Docker
│   ├── .env.example                      # Variables de entorno
│   ├── pytest.ini                       # Configuración de pruebas
│   ├── .coveragerc                      # Configuración de coverage
│   └── .gitignore                       # Archivos a ignorar
│
├── 🚀 SCRIPTS DE INSTALACIÓN
│   ├── setup.sh                         # Script de configuración (Linux/Mac)
│   └── setup.bat                        # Script de configuración (Windows)
│
├── 🏗️ CÓDIGO FUENTE
│   ├── manage.py                         # Script principal de Django
│   ├── erp_documents/                    # Configuración del proyecto
│   │   ├── settings/                     # Configuraciones por entorno
│   │   ├── urls.py                       # URLs principales
│   │   └── wsgi.py                       # Configuración WSGI
│   ├── companies/                        # Aplicación de empresas
│   │   ├── models.py                     # Modelos de datos
│   │   ├── serializers.py                # Serializers de API
│   │   ├── views.py                      # Vistas y ViewSets
│   │   ├── urls.py                       # URLs de la aplicación
│   │   ├── admin.py                      # Configuración del admin
│   │   └── migrations/                   # Migraciones de BD
│   ├── documents/                        # Aplicación de documentos
│   │   ├── models.py                     # Modelos de documentos
│   │   ├── serializers.py                # Serializers de documentos
│   │   ├── views.py                      # Vistas de documentos
│   │   ├── services.py                   # Servicios de cloud storage
│   │   ├── validation_service.py         # Lógica de validación
│   │   ├── urls.py                       # URLs de documentos
│   │   ├── admin.py                      # Admin de documentos
│   │   └── migrations/                   # Migraciones de documentos
│   └── tests/                           # Pruebas unitarias
│       ├── test_models.py                # Pruebas de modelos
│       ├── test_services.py              # Pruebas de servicios
│       └── test_views.py                 # Pruebas de API
│
└── 📊 ARCHIVOS DE CONFIGURACIÓN
    ├── static/                           # Archivos estáticos
    ├── media/                            # Archivos de media
    └── logs/                             # Archivos de log
```

## 🚀 Instrucciones de Instalación

### **Opción 1: Instalación Automática (Recomendada)**

#### **Windows:**
1. Abrir terminal como administrador
2. Navegar al directorio del proyecto
3. Ejecutar: `setup.bat`
4. Seguir las instrucciones en pantalla

#### **Linux/Mac:**
1. Abrir terminal
2. Navegar al directorio del proyecto
3. Ejecutar: `chmod +x setup.sh`
4. Ejecutar: `./setup.sh`
5. Seguir las instrucciones en pantalla

### **Opción 2: Instalación Manual**

#### **1. Configurar Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp env_example.txt .env

# Editar .env con tus credenciales
# Especialmente importante:
# - DATABASE_URL
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_STORAGE_BUCKET_NAME
```

#### **2. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

#### **3. Configurar Base de Datos**
```bash
# Crear base de datos PostgreSQL
createdb erp_documents

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

#### **4. Crear Datos de Prueba**
```bash
python manage.py shell
# Ejecutar el script de creación de datos de prueba
```

#### **5. Ejecutar Pruebas**
```bash
python manage.py test
coverage run --source='.' manage.py test
coverage report
```

### **Opción 3: Docker (Más Fácil)**

#### **1. Configurar Variables**
```bash
cp env_example.txt .env
# Editar .env con tus credenciales
```

#### **2. Iniciar Contenedores**
```bash
docker-compose up -d
```

#### **3. Ejecutar Migraciones**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## 🧪 Pruebas del Sistema

### **1. Pruebas con Postman**
1. Importar `ERP_Documents.postman_collection.json` en Postman
2. Seguir la guía en `GUIA_PRUEBAS_POSTMAN.md`
3. Configurar variables de entorno en Postman
4. Ejecutar el flujo completo de pruebas

### **2. Pruebas Unitarias**
```bash
# Ejecutar todas las pruebas
python manage.py test

# Ejecutar con coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### **3. Pruebas de API**
```bash
# Iniciar servidor
python manage.py runserver

# Probar endpoints manualmente
curl -X GET http://localhost:8000/api/companies/
```

## 🔧 Configuración Requerida

### **Credenciales Necesarias**

#### **Amazon S3:**
- `AWS_ACCESS_KEY_ID`: Clave de acceso de AWS
- `AWS_SECRET_ACCESS_KEY`: Clave secreta de AWS
- `AWS_STORAGE_BUCKET_NAME`: Nombre del bucket S3
- `AWS_S3_REGION_NAME`: Región de AWS (ej: us-east-1)

#### **Base de Datos:**
- `DATABASE_URL`: URL de conexión a PostgreSQL
- Ejemplo: `postgresql://user:password@localhost:5432/erp_documents`

#### **Django:**
- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: True para desarrollo, False para producción

### **Configuración de Bucket S3**

#### **1. Crear Bucket**
```bash
aws s3 mb s3://tu-bucket-name --region us-east-1
```

#### **2. Configurar Políticas**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::tu-bucket-name/*"
        }
    ]
}
```

## 📊 Datos de Prueba Incluidos

El sistema incluye datos de prueba automáticamente:

### **Empresa Demo:**
- Nombre: "Empresa Demo"
- NIT: "900123456-1"
- Email: "demo@empresa.com"

### **Usuarios Demo:**
- **Usuario Regular**: `demo_user` / `demo123`
- **Aprobador**: `demo_approver` / `demo123`

### **Entidades Demo:**
- **Vehículo**: "Vehículo Demo" (VEH001)
- **Empleado**: "Empleado Demo" (EMP001)

### **Tipos de Entidad:**
- **vehicle**: "Vehículo"
- **employee**: "Empleado"

## 🎯 Casos de Prueba Principales

### **1. Flujo Completo de Documento**
1. Generar URL de subida
2. Subir archivo a S3
3. Crear documento con validación
4. Aprobar documento
5. Descargar documento

### **2. Validación Jerárquica**
1. Crear documento con 3 pasos de validación
2. Aprobar con usuario de orden 2
3. Verificar aprobación automática de orden 1
4. Aprobar con usuario de orden 3
5. Verificar documento aprobado

### **3. Rechazo Terminal**
1. Crear documento con validación
2. Rechazar con cualquier aprobador
3. Verificar documento rechazado
4. Intentar aprobar (debe fallar)

## 🔍 Verificación de Funcionamiento

### **Checklist de Verificación:**

#### **✅ Configuración Base**
- [ ] Variables de entorno configuradas
- [ ] Base de datos conectada
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado

#### **✅ Cloud Storage**
- [ ] Credenciales AWS configuradas
- [ ] Bucket S3 creado y accesible
- [ ] URLs pre-firmadas funcionando

#### **✅ API REST**
- [ ] Servidor iniciado
- [ ] Endpoints respondiendo
- [ ] Autenticación funcionando
- [ ] Permisos por empresa funcionando

#### **✅ Funcionalidades**
- [ ] Subida de documentos
- [ ] Descarga de documentos
- [ ] Flujos de validación
- [ ] Aprobación jerárquica
- [ ] Rechazo terminal

#### **✅ Pruebas**
- [ ] Pruebas unitarias pasando
- [ ] Coverage > 95%
- [ ] Pruebas de Postman funcionando
- [ ] Admin de Django accesible

## 🚨 Solución de Problemas Comunes

### **Error de Conexión a BD**
```bash
# Verificar que PostgreSQL esté corriendo
sudo service postgresql status

# Verificar conexión
psql -h localhost -U usuario -d erp_documents
```

### **Error de Credenciales AWS**
```bash
# Verificar credenciales
aws sts get-caller-identity

# Verificar bucket
aws s3 ls s3://tu-bucket-name
```

### **Error de Migraciones**
```bash
# Resetear migraciones
python manage.py migrate --fake-initial

# Recrear migraciones
python manage.py makemigrations --empty companies
python manage.py makemigrations --empty documents
```

### **Error de Permisos**
```bash
# Verificar permisos de archivos
chmod +x setup.sh
chmod 755 logs/
chmod 755 media/
```

## 📞 Soporte y Contacto

### **Documentación Adicional**
- **README.md**: Documentación completa del sistema
- **RESUMEN_EJECUTIVO.md**: Resumen técnico del proyecto
- **GUIA_PRUEBAS_POSTMAN.md**: Guía detallada de pruebas

### **Archivos de Log**
- Los logs se guardan en `logs/erp_documents.log`
- Nivel de log configurable en variables de entorno
- Rotación automática de logs

### **Monitoreo**
- El sistema incluye logging detallado
- Métricas de rendimiento disponibles
- Alertas de errores configurable

## 🎉 ¡Sistema Listo para Usar!

Una vez completada la instalación, el sistema estará disponible en:

- **Admin de Django**: http://localhost:8000/admin/
- **API REST**: http://localhost:8000/api/
- **Documentación**: Ver archivos README.md y GUIA_PRUEBAS_POSTMAN.md

### **Credenciales por Defecto:**
- **Superusuario**: `admin` / `admin` (o las que configuraste)
- **Usuario Demo**: `demo_user` / `demo123`
- **Aprobador Demo**: `demo_approver` / `demo123`

---

**¡Disfruta usando el sistema ERP de gestión de documentos! 🚀**

*Desarrollado con excelencia técnica y atención al detalle.*
