# 🚀 GUÍA COMPLETA - ERP DOCUMENTS CON POSTGRESQL

## 📋 Resumen del Sistema

El sistema ERP de gestión de documentos ha sido configurado completamente con PostgreSQL y está listo para demostración. Incluye:

- ✅ Base de datos PostgreSQL configurada
- ✅ Usuarios y empresa demo creados
- ✅ Entidades (vehículo, empleado, equipo) configuradas
- ✅ Documentos de prueba con flujos de validación
- ✅ Simulación de almacenamiento S3
- ✅ Colección Postman completa

## 🗄️ Configuración de Base de Datos

### PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Base de datos**: erp_documents
- **Usuario**: postgres
- **Contraseña**: oscar3600

### Tablas Principales
- `companies_company` - Empresas
- `companies_user` - Usuarios del sistema
- `companies_entitytype` - Tipos de entidad
- `companies_entity` - Entidades (vehículos, empleados, equipos)
- `documents_document` - Documentos
- `documents_validationflow` - Flujos de validación
- `documents_validationstep` - Pasos de validación

## 👥 Usuarios del Sistema

| Usuario | Email | Contraseña | Rol |
|---------|-------|------------|-----|
| sustentador | sustentador@demo.com | sustentacion123 | Usuario principal |
| aprobador1 | aprobador1@demo.com | aprobador123 | Supervisor |
| aprobador2 | aprobador2@demo.com | aprobador123 | Gerente |
| admin | admin@demo.com | admin123 | Administrador |

## 🏢 Empresa Demo

- **ID**: `fb36990a-7101-4f07-9b1f-c58bf492355b`
- **Nombre**: Empresa Sustentación Demo
- **Email**: info@empresa-demo.com

## 🚗 Entidades Configuradas

### Vehículo Demo
- **ID**: `02d33ab1-4fc3-49e3-91b2-196d89c76b7b`
- **Tipo**: vehicle
- **Nombre**: Vehículo Demo

### Empleado Demo
- **ID**: `648eda80-bf9d-408d-92c4-089c6ab821b7`
- **Tipo**: employee
- **Nombre**: Empleado Demo

### Equipo Demo
- **ID**: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- **Tipo**: equipment
- **Nombre**: Equipo Demo

## 📄 Documentos de Prueba

### 1. SOAT Vehículo Demo
- **ID**: `05a7bcab-9015-4923-9bd3-ed54424d6fc7`
- **Nombre**: SOAT Vehículo Demo.pdf
- **Tamaño**: 245,760 bytes
- **Tipo**: application/pdf
- **Tags**: ["soat", "vehiculo", "seguro", "demo"]
- **Estado**: Pendiente de validación

### 2. Contrato Laboral Empleado
- **ID**: `b2c3d4e5-f6a7-8901-bcde-f23456789012`
- **Nombre**: Contrato Laboral Empleado.pdf
- **Tamaño**: 512,000 bytes
- **Tipo**: application/pdf
- **Tags**: ["contrato", "empleado", "laboral", "demo"]
- **Estado**: Pendiente de validación

### 3. Manual de Equipo
- **ID**: `c3d4e5f6-a7b8-9012-cdef-345678901234`
- **Nombre**: Manual de Equipo.pdf
- **Tamaño**: 1,024,000 bytes
- **Tipo**: application/pdf
- **Tags**: ["manual", "equipo", "procedimiento", "demo"]
- **Estado**: Pendiente de validación

## 🌐 Endpoints Principales

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión

### Empresas
- `GET /api/companies/` - Listar empresas
- `GET /api/companies/{id}/` - Obtener empresa

### Entidades
- `GET /api/entities/?company_id={id}` - Listar entidades
- `GET /api/entities/{id}/` - Obtener entidad

### Documentos
- `GET /api/documents/?company_id={id}` - Listar documentos
- `GET /api/documents/{id}/` - Obtener documento
- `POST /api/documents/` - Crear documento
- `PATCH /api/documents/{id}/` - Actualizar documento
- `DELETE /api/documents/{id}/` - Eliminar documento
- `GET /api/documents/{id}/download/` - Descargar documento

### Validaciones
- `GET /api/validation-flows/?company_id={id}` - Listar flujos
- `POST /api/validation-steps/{id}/action/` - Ejecutar acción

## 🚀 Inicio Rápido

### 1. Iniciar Servidor
```bash
# Opción 1: Script automático
start_server_postgresql.bat

# Opción 2: Manual
venv\Scripts\activate
python manage.py runserver 8000
```

### 2. Importar en Postman
1. Importar colección: `ERP_Documents_PostgreSQL.postman_collection.json`
2. Importar entorno: `ERP_Documents_PostgreSQL.postman_environment.json`
3. Seleccionar entorno "ERP Documents PostgreSQL Environment"

### 3. Flujo de Prueba Recomendado
1. **Login** - Ejecutar "Login - Sustentador"
2. **Empresas** - Ejecutar "Listar Empresas"
3. **Entidades** - Ejecutar "Listar Entidades"
4. **Documentos** - Ejecutar "Listar Documentos"
5. **Crear Documento** - Ejecutar "Crear Nuevo Documento"
6. **Validaciones** - Ejecutar "Listar Flujos de Validación"

## 📊 Estadísticas del Sistema

- **Archivos simulados**: 3
- **Tamaño total**: 1,781,760 bytes (~1.7 MB)
- **Tipos MIME**: 1 (application/pdf)
- **Flujos de validación**: 3 (uno por documento)
- **Pasos de validación**: 9 (3 pasos por documento)

## 🔧 Comandos Útiles

### Verificar Estado de la Base de Datos
```bash
psql -U postgres -h localhost -d erp_documents -c "SELECT COUNT(*) FROM documents_document;"
```

### Reinicializar Sistema
```bash
python init_postgresql_completo.py
```

### Ver Logs del Servidor
```bash
python manage.py runserver 8000 --verbosity=2
```

## 🎯 Casos de Uso para Demostración

### 1. Gestión de Documentos
- Crear nuevo documento
- Actualizar metadatos
- Descargar archivo
- Eliminar documento

### 2. Flujo de Validación
- Aprobar documento
- Rechazar documento
- Ver historial de validaciones

### 3. Reportes
- Estadísticas de documentos
- Reportes de validación
- Métricas por entidad

## 🚨 Solución de Problemas

### Error de Conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté ejecutándose
psql -U postgres -h localhost -c "SELECT version();"
```

### Error de Token de Autenticación
1. Ejecutar "Login - Sustentador" primero
2. Verificar que el token se guardó en las variables de entorno

### Error 404 en Documentos
1. Verificar que el documento existe en la base de datos
2. Confirmar que el archivo está simulado en el almacenamiento

## 📞 Soporte

Para cualquier problema o pregunta sobre el sistema:
1. Verificar logs del servidor Django
2. Revisar conexión a PostgreSQL
3. Ejecutar script de diagnóstico: `python diagnostico.py`

---

**¡El sistema está listo para demostración! 🎉**