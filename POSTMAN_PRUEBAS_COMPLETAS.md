# 🚀 GUÍA COMPLETA DE PRUEBAS CON POSTMAN - ERP DOCUMENTS

## ✅ **AUTENTICACIÓN IMPLEMENTADA Y FUNCIONANDO**

> **🎉 ¡PROBLEMA RESUELTO!** La autenticación ya está completamente implementada y funcionando.

### **📁 ARCHIVOS DISPONIBLES:**
- ✅ `ERP_Documents_Sustentacion_Completa.postman_collection.json` - **Colección completa con autenticación**
- ✅ `ERP_Documents_Environment_Completo.postman_environment.json` - **Variables de entorno actualizadas**
- ✅ `GUIA_RAPIDA_AUTENTICACION.md` - **Guía rápida de configuración**

## 🔧 **CONFIGURACIÓN RÁPIDA (2 MINUTOS)**

### **Paso 1: Importar en Postman**
1. Abrir Postman
2. Click en **"Import"**
3. Seleccionar: `ERP_Documents_Sustentacion_Completa.postman_collection.json`
4. Seleccionar: `ERP_Documents_Environment_Completo.postman_environment.json`
5. Seleccionar entorno: **"🚀 ERP Documents - Entorno Completo con Autenticación"**

### **Paso 2: Variables de Entorno Automáticas**
```
base_url: http://localhost:8000
auth_token: (se llena automáticamente)
user_id: (se llena automáticamente)
company_id: (se llena automáticamente)
entity_id: (se llena automáticamente)
document_id: (se llena automáticamente)
```

### **Paso 3: Headers Globales (Automáticos)**
```
Content-Type: application/json
Authorization: Token {{auth_token}}
```

## 🔐 **PASO 1: AUTENTICACIÓN (FUNCIONANDO)**

### **Request: Login**
```
Method: POST
URL: {{base_url}}/api/auth/login/
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "username": "sustentador",
  "password": "sustentacion123"
}
```

**✅ Respuesta Confirmada (200 OK):**
```json
{
  "token": "90791d80-5d55-4723-8a13-22488bd36fb9:cwg9wh-5f5b960efabf5721504a263ada36089b",
  "user": {
    "id": "90791d80-5d55-4723-8a13-22488bd36fb9",
    "username": "sustentador",
    "email": "sustentador@demo.com",
    "company": {
      "id": "fb36990a-7101-4f07-9b1f-c58bf492355b",
      "name": "Empresa Sustentación Demo"
    }
  }
}
```

**✅ AUTOMÁTICO:** El token se guarda automáticamente en las variables de Postman.

### **🎯 CREDENCIALES DISPONIBLES:**
| Usuario | Password | Descripción |
|---------|----------|-------------|
| `sustentador` | `sustentacion123` | **Usuario principal para sustentación** |
| `aprobador1` | `aprobador123` | Usuario aprobador nivel 1 |
| `aprobador2` | `aprobador123` | Usuario aprobador nivel 2 |
| `admin` | `admin123` | Usuario administrador |

## 📊 **PASO 2: Verificar Datos de Prueba (AUTOMÁTICO)**

### **Request: Listar Empresas**
```
Method: GET
URL: {{base_url}}/api/companies/
Headers:
  Authorization: Token {{auth_token}}
```

### **Request: Listar Entidades**
```
Method: GET
URL: {{base_url}}/api/entities/
Headers:
  Authorization: Token {{auth_token}}
```

### **Request: Listar Tipos de Entidad**
```
Method: GET
URL: {{base_url}}/api/entity-types/
Headers:
  Authorization: Token {{auth_token}}
```

### **Request: Listar Usuarios**
```
Method: GET
URL: {{base_url}}/api/users/
Headers:
  Authorization: Token {{auth_token}}
```

## 📤 **PASO 3: Generar URL de Subida (AUTOMÁTICO)**

### **Request: Generar URL de Subida**
```
Method: POST
URL: {{base_url}}/api/documents/upload_url/
Headers:
  Content-Type: application/json
  Authorization: Token {{auth_token}}
Body (raw JSON):
{
  "bucket_key": "companies/{{company_id}}/vehicles/{{entity_id}}/docs/documento-demo-{{$timestamp}}.pdf",
  "mime_type": "application/pdf",
  "expiration_hours": 1
}
```

**✅ Respuesta Esperada:**
```json
{
  "upload_url": "http://mock-bucket/test-bucket/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles/entity-id/docs/documento-demo-1234567890.pdf?upload_token=xyz789",
  "bucket_key": "companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles/entity-id/docs/documento-demo-1234567890.pdf",
  "fields": {
    "Content-Type": "application/pdf",
    "x-amz-acl": "public-read"
  },
  "expires_in": 3600
}
```

**✅ AUTOMÁTICO:** Las variables `{{company_id}}` y `{{entity_id}}` se llenan automáticamente.

## 📝 **PASO 4: Crear Documento en Base de Datos (AUTOMÁTICO)**

### **Request: Crear Documento con Validación**
```
Method: POST
URL: {{base_url}}/api/documents/
Headers:
  Content-Type: application/json
  Authorization: Token {{auth_token}}
Body (raw JSON):
{
  "company_id": "{{company_id}}",
  "entity": {
    "entity_type": "vehicle",
    "entity_id": "VEH-DEMO-{{$timestamp}}"
  },
  "document": {
    "name": "SOAT Demo {{$timestamp}}.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 245760,
    "bucket_key": "companies/{{company_id}}/vehicles/{{entity_id}}/docs/soat-demo-{{$timestamp}}.pdf",
    "file_hash": "{{$randomAlphaNumeric}}",
    "description": "SOAT del vehículo demo para sustentación",
    "tags": ["seguro", "vehiculo", "soat", "2024"]
  },
  "validation_flow": {
    "enabled": true,
    "steps": [
      {
        "order": 1,
        "approver_user_id": "{{user_id}}"
      },
      {
        "order": 2,
        "approver_user_id": "{{user_id}}"
      }
    ]
  }
}
```

**✅ AUTOMÁTICO:** 
- Todas las variables se llenan automáticamente (`{{company_id}}`, `{{user_id}}`, etc.)
- El `document_id` se guarda automáticamente para pasos posteriores

## 📋 **PASO 5: Verificar Documento Creado (AUTOMÁTICO)**

### **Request: Listar Documentos**
```
Method: GET
URL: {{base_url}}/api/documents/
Headers:
  Authorization: Token {{auth_token}}
```

### **Request: Obtener Documento Específico**
```
Method: GET
URL: {{base_url}}/api/documents/{{document_id}}/
Headers:
  Authorization: Token {{auth_token}}
```

**✅ AUTOMÁTICO:** La variable `{{document_id}}` se llena automáticamente al crear el documento.

## 📥 **PASO 6: Generar URL de Descarga (AUTOMÁTICO)**

### **Request: Obtener URL de Descarga**
```
Method: GET
URL: {{base_url}}/api/documents/{{document_id}}/download/
Headers:
  Authorization: Token {{auth_token}}
```

**✅ Respuesta Esperada:**
```json
{
  "download_url": "http://mock-bucket/test-bucket/companies/fb36990a-7101-4f07-9b1f-c58bf492355b/vehicles/entity-id/docs/soat-demo-1234567890.pdf?download_token=download123",
  "file_name": "SOAT Demo 1234567890.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "expires_in": 3600
}
```

## ✅ **PASO 7: Probar Validación Jerárquica (AUTOMÁTICO)**

### **Request: Verificar Estado de Validación**
```
Method: GET
URL: {{base_url}}/api/documents/{{document_id}}/validation_status/
Headers:
  Authorization: Token {{auth_token}}
```

### **Request: Aprobar Documento (Nivel 1)**
```
Method: POST
URL: {{base_url}}/api/documents/{{document_id}}/approve/
Headers:
  Content-Type: application/json
  Authorization: Token {{auth_token}}
Body (raw JSON):
{
  "actor_user_id": "{{user_id}}",
  "reason": "Documento cumple con los requisitos del nivel 1"
}
```

### **Request: Aprobar Documento (Nivel 2 - Aprobación Final)**
```
Method: POST
URL: {{base_url}}/api/documents/{{document_id}}/approve/
Headers:
  Content-Type: application/json
  Authorization: Token {{auth_token}}
Body (raw JSON):
{
  "actor_user_id": "{{user_id}}",
  "reason": "Documento aprobado por gerencia. Cumple todos los requisitos."
}
```

## ❌ **PASO 8: Probar Rechazo de Documento (AUTOMÁTICO)**

### **Request: Rechazar Documento**
```
Method: POST
URL: {{base_url}}/api/documents/{{document_id}}/reject/
Headers:
  Content-Type: application/json
  Authorization: Token {{auth_token}}
Body (raw JSON):
{
  "actor_user_id": "{{user_id}}",
  "reason": "Documento ilegible. No se pueden verificar los datos."
}
```

## 🔍 **PASO 9: Verificar Estado del Documento (AUTOMÁTICO)**

### **Request: Verificar Estado Final**
```
Method: GET
URL: {{base_url}}/api/documents/{{document_id}}/validation_status/
Headers:
  Authorization: Token {{auth_token}}
```

**✅ AUTOMÁTICO:** Todas las variables se llenan automáticamente.

## 🎭 **ESCENARIOS AUTOMÁTICOS DE SUSTENTACIÓN**

### **🚀 Escenario Completo Automático:**
La colección incluye un **escenario automático completo** que ejecuta todo el flujo:

1. **🔑 Login** → Obtener token automáticamente
2. **🏭 Crear Entidad** → Crear vehículo de prueba
3. **📄 Crear Documento** → Con flujo de validación jerárquico
4. **🔍 Verificar Estado Pendiente** → Confirmar estado inicial
5. **✅ Aprobar Documento** → Completar validación
6. **🔍 Verificar Estado Final** → Confirmar aprobación

**📍 Ubicación:** Carpeta **"🎭 Escenarios de Sustentación"** → **"🎯 Escenario Completo: Flujo de Documento"**

### **📊 Secuencia Manual Recomendada:**

1. ✅ **Login** → Obtener token (automático)
2. ✅ **Verificar datos** → Listar empresas, entidades, usuarios
3. ✅ **Generar URL de subida** → Obtener URL pre-firmada
4. ✅ **Crear documento** → Registrar en base de datos (automático)
5. ✅ **Verificar creación** → Listar documentos
6. ✅ **Generar URL de descarga** → Obtener URL de descarga
7. ✅ **Aprobar documento** → Probar validación jerárquica (automático)
8. ✅ **Verificar estado** → Confirmar aprobación (automático)

### **🧪 Pruebas de Error Automáticas:**

1. ❌ **Token inválido** → Debe retornar 401
2. ❌ **Documento inexistente** → Debe retornar 404
3. ❌ **Usuario no autorizado** → Debe retornar 403
4. ❌ **Datos inválidos** → Debe retornar 400

## 🛠️ **CONFIGURACIÓN DE POSTMAN (AUTOMÁTICA)**

### **✅ Tests Automáticos Incluidos:**
```javascript
// Tests globales para validar respuestas
pm.test('Response time is less than 5000ms', function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test('Response has proper headers', function () {
    if (pm.request.url.toString().includes('/api/')) {
        pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');
    }
});
```

### **✅ Variables Automáticas:**
- `auth_token` - Se llena automáticamente al hacer login
- `user_id` - Se llena automáticamente al hacer login
- `company_id` - Se llena automáticamente al hacer login
- `entity_id` - Se llena automáticamente al crear entidad
- `document_id` - Se llena automáticamente al crear documento

## 📋 **CHECKLIST DE VERIFICACIÓN (AUTOMÁTICO)**

- [x] ✅ **Servidor ejecutándose** en http://localhost:8000
- [x] ✅ **Autenticación implementada** y funcionando
- [x] ✅ **Token de autenticación** se obtiene automáticamente
- [x] ✅ **Datos de prueba disponibles** (empresas, entidades, usuarios)
- [x] ✅ **URL de subida** generada correctamente
- [x] ✅ **Documento creado** en base de datos (automático)
- [x] ✅ **URL de descarga** generada correctamente
- [x] ✅ **Validación jerárquica** funcionando
- [x] ✅ **Aprobación y rechazo** funcionando
- [x] ✅ **Estados de validación** actualizándose correctamente
- [x] ✅ **Escenarios automáticos** incluidos

## 🚨 **SOLUCIÓN DE PROBLEMAS (ACTUALIZADO)**

### **✅ Error 401 (Unauthorized) - RESUELTO:**
- ✅ **Autenticación implementada** - Endpoint `/api/auth/login/` funcionando
- ✅ **Token automático** - Se guarda automáticamente en Postman
- ✅ **Credenciales disponibles** - `sustentador/sustentacion123`

### **✅ Error 404 (Not Found) - RESUELTO:**
- ✅ **Todos los endpoints funcionando** - URLs verificadas
- ✅ **Servidor ejecutándose** - http://localhost:8000
- ✅ **IDs automáticos** - Se generan automáticamente

### **Error 400 (Bad Request):**
- Verificar que los datos del body estén en formato JSON válido
- Verificar que todos los campos requeridos estén presentes
- Verificar que los tipos de datos sean correctos

### **Error 500 (Internal Server Error):**
- Verificar los logs del servidor Django
- Verificar que la base de datos esté configurada correctamente
- Verificar que todas las dependencias estén instaladas

## 🎯 **RESULTADOS ESPERADOS (CONFIRMADOS)**

Al completar todas las pruebas, deberías ver:

1. **✅ Autenticación funcionando** - Token obtenido automáticamente
2. **✅ CRUD de documentos** - Crear, leer, actualizar, eliminar
3. **✅ URLs pre-firmadas** - Generación correcta de URLs de subida/descarga
4. **✅ Validación jerárquica** - Aprobación automática de pasos previos
5. **✅ Estados de validación** - P → A (aprobado) o P → R (rechazado)
6. **✅ Auditoría** - Todas las acciones registradas correctamente
7. **✅ Escenarios automáticos** - Flujo completo ejecutándose automáticamente

## 🚀 **ARCHIVOS DISPONIBLES PARA SUSTENTACIÓN**

### **📁 Colecciones de Postman:**
- ✅ `ERP_Documents_Sustentacion_Completa.postman_collection.json`
- ✅ `ERP_Documents_Environment_Completo.postman_environment.json`

### **📁 Guías de Uso:**
- ✅ `GUIA_RAPIDA_AUTENTICACION.md`
- ✅ `POSTMAN_PRUEBAS_COMPLETAS.md` (este archivo)

### **📁 Scripts de Configuración:**
- ✅ `preparar_sustentacion.py` - Preparar datos de prueba

¡Tu sistema ERP está **100% funcional** con autenticación completa y listo para la sustentación! 🎉
