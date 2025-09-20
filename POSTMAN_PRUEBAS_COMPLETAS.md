# 🚀 GUÍA COMPLETA DE PRUEBAS CON POSTMAN - ERP DOCUMENTS

## 🔧 **CONFIGURACIÓN INICIAL**

### 1. **Variables de Entorno en Postman**
```
BASE_URL: http://localhost:8000
API_BASE: {{BASE_URL}}/api
TOKEN: (se obtendrá después del login)
```

### 2. **Headers Globales**
```
Content-Type: application/json
Authorization: Token {{TOKEN}}
```

## 🔐 **PASO 1: Obtener Token de Autenticación**

### **Request: Login**
```
Method: POST
URL: {{BASE_URL}}/api/auth/token/
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "username": "admin",
  "password": "admin123"
}
```

**Respuesta Esperada:**
```json
{
  "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
}
```

**⚠️ IMPORTANTE:** Copia el token y pégalo en la variable `TOKEN` de Postman.

## 📊 **PASO 2: Verificar Datos de Prueba**

### **Request: Listar Empresas**
```
Method: GET
URL: {{API_BASE}}/companies/
Headers:
  Authorization: Token {{TOKEN}}
```

### **Request: Listar Entidades**
```
Method: GET
URL: {{API_BASE}}/companies/entities/
Headers:
  Authorization: Token {{TOKEN}}
```

### **Request: Listar Usuarios**
```
Method: GET
URL: {{API_BASE}}/companies/users/
Headers:
  Authorization: Token {{TOKEN}}
```

## 📤 **PASO 3: Generar URL de Subida**

### **Request: Generar URL de Subida**
```
Method: POST
URL: {{API_BASE}}/documents/upload-url/
Headers:
  Content-Type: application/json
  Authorization: Token {{TOKEN}}
Body (raw JSON):
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity": {
    "entity_type": "vehicle",
    "entity_id": "VEH001"
  },
  "file_name": "soat_2024.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1048576
}
```

**Respuesta Esperada:**
```json
{
  "upload_url": "http://mock-bucket/test-bucket/companies/550e8400-e29b-41d4-a716-446655440000/vehicle/VEH001/abc123-def456/soat_2024.pdf?upload_token=xyz789",
  "bucket_key": "companies/550e8400-e29b-41d4-a716-446655440000/vehicle/VEH001/abc123-def456/soat_2024.pdf",
  "fields": {
    "Content-Type": "application/pdf",
    "x-amz-acl": "public-read"
  },
  "expires_in": 3600
}
```

**⚠️ IMPORTANTE:** Guarda el `bucket_key` para el siguiente paso.

## 📝 **PASO 4: Crear Documento en Base de Datos**

### **Request: Crear Documento**
```
Method: POST
URL: {{API_BASE}}/documents/
Headers:
  Content-Type: application/json
  Authorization: Token {{TOKEN}}
Body (raw JSON):
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity": {
    "entity_type": "vehicle",
    "entity_id": "VEH001"
  },
  "document": {
    "name": "soat_2024.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 1048576,
    "bucket_key": "companies/550e8400-e29b-41d4-a716-446655440000/vehicle/VEH001/abc123-def456/soat_2024.pdf",
    "file_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
    "description": "SOAT del vehículo para el año 2024",
    "tags": ["seguro", "vehiculo", "2024"]
  },
  "validation_flow": {
    "enabled": true,
    "steps": [
      {
        "order": 1,
        "approver_user_id": "user1-uuid-here"
      },
      {
        "order": 2,
        "approver_user_id": "user2-uuid-here"
      }
    ]
  }
}
```

**⚠️ IMPORTANTE:** 
- Reemplaza `"user1-uuid-here"` y `"user2-uuid-here"` con los UUIDs reales de los usuarios de prueba
- Usa el `bucket_key` del paso anterior

## 📋 **PASO 5: Verificar Documento Creado**

### **Request: Listar Documentos**
```
Method: GET
URL: {{API_BASE}}/documents/
Headers:
  Authorization: Token {{TOKEN}}
```

### **Request: Obtener Documento Específico**
```
Method: GET
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/
Headers:
  Authorization: Token {{TOKEN}}
```

**⚠️ IMPORTANTE:** Reemplaza `{DOCUMENT_ID}` con el ID real del documento creado.

## 📥 **PASO 6: Generar URL de Descarga**

### **Request: Obtener URL de Descarga**
```
Method: GET
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/download/
Headers:
  Authorization: Token {{TOKEN}}
```

**Respuesta Esperada:**
```json
{
  "download_url": "http://mock-bucket/test-bucket/companies/550e8400-e29b-41d4-a716-446655440000/vehicle/VEH001/abc123-def456/soat_2024.pdf?download_token=download123",
  "file_name": "soat_2024.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1048576,
  "expires_in": 3600
}
```

## ✅ **PASO 7: Probar Validación Jerárquica**

### **Request: Aprobar Documento (Nivel 1)**
```
Method: POST
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/approve/
Headers:
  Content-Type: application/json
  Authorization: Token {{TOKEN}}
Body (raw JSON):
{
  "actor_user_id": "user1-uuid-here",
  "reason": "Documento cumple con los requisitos del nivel 1"
}
```

### **Request: Aprobar Documento (Nivel 2 - Aprobación Final)**
```
Method: POST
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/approve/
Headers:
  Content-Type: application/json
  Authorization: Token {{TOKEN}}
Body (raw JSON):
{
  "actor_user_id": "user2-uuid-here",
  "reason": "Documento aprobado por gerencia. Cumple todos los requisitos."
}
```

## ❌ **PASO 8: Probar Rechazo de Documento**

### **Request: Rechazar Documento**
```
Method: POST
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/reject/
Headers:
  Content-Type: application/json
  Authorization: Token {{TOKEN}}
Body (raw JSON):
{
  "actor_user_id": "user1-uuid-here",
  "reason": "Documento ilegible. No se pueden verificar los datos."
}
```

## 🔍 **PASO 9: Verificar Estado del Documento**

### **Request: Verificar Estado**
```
Method: GET
URL: {{API_BASE}}/documents/{DOCUMENT_ID}/
Headers:
  Authorization: Token {{TOKEN}}
```

## 📊 **SECUENCIA DE PRUEBAS RECOMENDADA**

### **Flujo Completo de Pruebas:**

1. ✅ **Login** → Obtener token
2. ✅ **Verificar datos** → Listar empresas, entidades, usuarios
3. ✅ **Generar URL de subida** → Obtener URL pre-firmada
4. ✅ **Crear documento** → Registrar en base de datos
5. ✅ **Verificar creación** → Listar documentos
6. ✅ **Generar URL de descarga** → Obtener URL de descarga
7. ✅ **Aprobar documento** → Probar validación jerárquica
8. ✅ **Verificar estado** → Confirmar aprobación

### **Pruebas de Error:**

1. ❌ **Token inválido** → Debe retornar 401
2. ❌ **Documento inexistente** → Debe retornar 404
3. ❌ **Usuario no autorizado** → Debe retornar 403
4. ❌ **Datos inválidos** → Debe retornar 400

## 🛠️ **CONFIGURACIÓN DE POSTMAN**

### **Pre-request Script (Global):**
```javascript
// Verificar que el token existe
if (!pm.environment.get("TOKEN")) {
    console.log("⚠️ Token no encontrado. Ejecuta primero el login.");
}
```

### **Tests (Global):**
```javascript
// Test para verificar respuesta exitosa
pm.test("Status code is 200 or 201", function () {
    pm.expect(pm.response.code).to.be.oneOf([200, 201]);
});

// Test para verificar que la respuesta es JSON
pm.test("Response is JSON", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});
```

## 📋 **CHECKLIST DE VERIFICACIÓN**

- [ ] ✅ Servidor ejecutándose en http://localhost:8000
- [ ] ✅ Token de autenticación obtenido
- [ ] ✅ Datos de prueba disponibles (empresas, entidades, usuarios)
- [ ] ✅ URL de subida generada correctamente
- [ ] ✅ Documento creado en base de datos
- [ ] ✅ URL de descarga generada correctamente
- [ ] ✅ Validación jerárquica funcionando
- [ ] ✅ Aprobación y rechazo funcionando
- [ ] ✅ Estados de validación actualizándose correctamente

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### **Error 401 (Unauthorized):**
- Verificar que el token esté configurado correctamente
- Verificar que el token no haya expirado
- Ejecutar nuevamente el login

### **Error 404 (Not Found):**
- Verificar que el servidor esté ejecutándose
- Verificar que las URLs estén correctas
- Verificar que los IDs existan en la base de datos

### **Error 400 (Bad Request):**
- Verificar que los datos del body estén en formato JSON válido
- Verificar que todos los campos requeridos estén presentes
- Verificar que los tipos de datos sean correctos

### **Error 500 (Internal Server Error):**
- Verificar los logs del servidor Django
- Verificar que la base de datos esté configurada correctamente
- Verificar que todas las dependencias estén instaladas

## 🎯 **RESULTADOS ESPERADOS**

Al completar todas las pruebas, deberías ver:

1. **✅ Autenticación funcionando** - Token obtenido correctamente
2. **✅ CRUD de documentos** - Crear, leer, actualizar, eliminar
3. **✅ URLs pre-firmadas** - Generación correcta de URLs de subida/descarga
4. **✅ Validación jerárquica** - Aprobación automática de pasos previos
5. **✅ Estados de validación** - P → A (aprobado) o P → R (rechazado)
6. **✅ Auditoría** - Todas las acciones registradas correctamente

¡Con esta guía puedes verificar completamente el funcionamiento del sistema desde Postman! 🚀
