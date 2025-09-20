# Guía de Pruebas para el Sistema ERP de Gestión de Documentos

## Descripción General

Este documento proporciona una guía completa para probar el sistema ERP de gestión de documentos utilizando Postman. El sistema permite subir, gestionar y validar documentos mediante flujos jerárquicos de aprobación.

## Configuración Inicial

### 1. Importar la Colección de Postman

1. Abre Postman
2. Haz clic en "Import"
3. Selecciona el archivo `ERP_Documents.postman_collection.json`
4. La colección se importará con todos los endpoints configurados

### 2. Configurar Variables de Entorno

Antes de comenzar las pruebas, configura las siguientes variables en Postman:

- `base_url`: `http://localhost:8000` (o la URL de tu servidor)
- `auth_token`: Se llenará automáticamente después del login
- `company_id`: ID de la empresa (se obtiene de la respuesta de login)
- `entity_id`: ID de la entidad (se obtiene al crear entidades)
- `entity_type_id`: ID del tipo de entidad (se obtiene al listar tipos)
- `user_id`: ID del usuario (se obtiene al crear usuarios)
- `document_id`: ID del documento (se obtiene al crear documentos)
- `approver_user_id`: ID del aprobador (se obtiene al crear usuarios aprobadores)
- `approver_user_id_2`: ID del segundo aprobador (opcional)

## Flujo de Pruebas Completo

### Paso 1: Configuración Inicial

#### 1.1 Crear Empresa (Admin)
```bash
# Si no tienes una empresa, créala desde el admin de Django
# O usa la empresa existente en la base de datos
```

#### 1.2 Crear Usuarios
1. **Crear Usuario Regular**:
   - Endpoint: `POST /api/users/`
   - Body:
   ```json
   {
       "username": "testuser",
       "email": "test@test.com",
       "password": "testpass123",
       "first_name": "Test",
       "last_name": "User",
       "company_id": "{{company_id}}",
       "employee_id": "EMP001",
       "phone": "+57 300 123 4567",
       "position": "Analista",
       "department": "TI"
   }
   ```

2. **Crear Usuario Aprobador**:
   - Endpoint: `POST /api/users/`
   - Body:
   ```json
   {
       "username": "approver",
       "email": "approver@test.com",
       "password": "testpass123",
       "first_name": "Approver",
       "last_name": "User",
       "company_id": "{{company_id}}",
       "employee_id": "EMP002",
       "phone": "+57 300 123 4568",
       "position": "Supervisor",
       "department": "TI",
       "is_company_admin": true
   }
   ```

#### 1.3 Crear Tipo de Entidad
1. **Listar Tipos de Entidad**:
   - Endpoint: `GET /api/entity-types/`
   - Guarda el `entity_type_id` de "vehicle" en las variables

#### 1.4 Crear Entidad
1. **Crear Entidad**:
   - Endpoint: `POST /api/entities/`
   - Body:
   ```json
   {
       "entity_type_id": "{{entity_type_id}}",
       "external_id": "VEH001",
       "name": "Vehículo Test",
       "metadata": {
           "brand": "Toyota",
           "model": "Corolla",
           "year": 2023
       }
   }
   ```

### Paso 2: Autenticación

#### 2.1 Login
1. **Hacer Login**:
   - Endpoint: `POST /api/auth/login/`
   - Body:
   ```json
   {
       "username": "testuser",
       "password": "testpass123"
   }
   ```
2. **Guardar el token** en la variable `auth_token`

### Paso 3: Gestión de Documentos

#### 3.1 Generar URL de Subida
1. **Generar URL Pre-firmada**:
   - Endpoint: `POST /api/documents/upload_url/`
   - Body:
   ```json
   {
       "company_id": "{{company_id}}",
       "entity_type": "vehicle",
       "entity_id": "VEH001",
       "filename": "soat.pdf",
       "mime_type": "application/pdf",
       "size_bytes": 123456
   }
   ```
2. **Guardar el `bucket_key`** para usar en el siguiente paso

#### 3.2 Crear Documento con Validación
1. **Crear Documento**:
   - Endpoint: `POST /api/documents/`
   - Body:
   ```json
   {
       "company_id": "{{company_id}}",
       "entity": {
           "entity_type": "vehicle",
           "entity_id": "VEH001"
       },
       "document": {
           "name": "soat.pdf",
           "mime_type": "application/pdf",
           "size_bytes": 123456,
           "bucket_key": "{{bucket_key_from_previous_step}}",
           "description": "SOAT del vehículo",
           "tags": ["seguro", "vehiculo", "soat"]
       },
       "validation_flow": {
           "enabled": true,
           "steps": [
               {
                   "order": 1,
                   "approver_user_id": "{{approver_user_id}}"
               },
               {
                   "order": 2,
                   "approver_user_id": "{{approver_user_id_2}}"
               }
           ]
       }
   }
   ```

#### 3.3 Crear Documento sin Validación
1. **Crear Documento Simple**:
   - Endpoint: `POST /api/documents/`
   - Body:
   ```json
   {
       "company_id": "{{company_id}}",
       "entity": {
           "entity_type": "vehicle",
           "entity_id": "VEH001"
       },
       "document": {
           "name": "manual.pdf",
           "mime_type": "application/pdf",
           "size_bytes": 98765,
           "bucket_key": "companies/{{company_id}}/vehicles/VEH001/docs/manual.pdf",
           "description": "Manual del vehículo"
       }
   }
   ```

### Paso 4: Validación de Documentos

#### 4.1 Verificar Estado de Validación
1. **Obtener Estado**:
   - Endpoint: `GET /api/documents/{{document_id}}/validation_status/`
   - Verifica que el estado sea "P" (Pendiente)

#### 4.2 Aprobar Documento
1. **Hacer Login como Aprobador**:
   - Cambia las credenciales a las del usuario aprobador
   - Endpoint: `POST /api/auth/login/`

2. **Aprobar Documento**:
   - Endpoint: `POST /api/documents/{{document_id}}/approve/`
   - Body:
   ```json
   {
       "actor_user_id": "{{approver_user_id}}",
       "reason": "Documento cumple con todos los requisitos"
   }
   ```

#### 4.3 Verificar Aprobación
1. **Verificar Estado**:
   - Endpoint: `GET /api/documents/{{document_id}}/validation_status/`
   - Verifica que el estado sea "A" (Aprobado)

### Paso 5: Pruebas de Rechazo

#### 5.1 Crear Documento para Rechazo
1. **Crear Nuevo Documento**:
   - Repite el paso 3.2 con un documento diferente
   - Guarda el nuevo `document_id`

#### 5.2 Rechazar Documento
1. **Rechazar Documento**:
   - Endpoint: `POST /api/documents/{{document_id}}/reject/`
   - Body:
   ```json
   {
       "actor_user_id": "{{approver_user_id}}",
       "reason": "Documento ilegible, calidad de imagen insuficiente"
   }
   ```

#### 5.3 Verificar Rechazo
1. **Verificar Estado**:
   - Endpoint: `GET /api/documents/{{document_id}}/validation_status/`
   - Verifica que el estado sea "R" (Rechazado)

### Paso 6: Pruebas de Descarga

#### 6.1 Generar URL de Descarga
1. **Obtener URL de Descarga**:
   - Endpoint: `GET /api/documents/{{document_id}}/download/`
   - Verifica que se genere una URL pre-firmada válida

### Paso 7: Pruebas de Estadísticas

#### 7.1 Estadísticas de Usuario
1. **Obtener Estadísticas**:
   - Endpoint: `GET /api/users/{{user_id}}/approval_stats/`
   - Verifica los contadores de aprobaciones/rechazos

#### 7.2 Documentos Pendientes
1. **Obtener Pendientes**:
   - Endpoint: `GET /api/documents/pending_approvals/`
   - Verifica que aparezcan los documentos pendientes

#### 7.3 Estadísticas de Empresa
1. **Obtener Estadísticas de Empresa**:
   - Endpoint: `GET /api/companies/{{company_id}}/stats/`
   - Verifica los contadores de usuarios, documentos y entidades

## Casos de Prueba Específicos

### Caso 1: Flujo de Validación Jerárquico
1. Crear documento con 3 pasos de validación
2. Aprobar con usuario de orden 2 (debe aprobar automáticamente orden 1)
3. Verificar que orden 3 sigue pendiente
4. Aprobar con usuario de orden 3
5. Verificar que el documento queda aprobado

### Caso 2: Rechazo Terminal
1. Crear documento con flujo de validación
2. Rechazar con cualquier aprobador
3. Verificar que el documento queda rechazado
4. Intentar aprobar (debe fallar)

### Caso 3: Validación de Permisos
1. Intentar aprobar documento con usuario que no es aprobador
2. Verificar que se recibe error 400
3. Intentar acceder a documentos de otra empresa
4. Verificar que no se muestran documentos

### Caso 4: Validación de Datos
1. Intentar crear documento con tipo MIME inválido
2. Intentar crear documento con tamaño excesivo
3. Intentar crear documento con empresa inexistente
4. Verificar que se reciben errores apropiados

## Códigos de Respuesta Esperados

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `204 No Content`: Recurso eliminado exitosamente
- `400 Bad Request`: Error en los datos enviados
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: Sin permisos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error interno del servidor

## Notas Importantes

1. **Orden de Ejecución**: Las pruebas deben ejecutarse en el orden indicado para que las variables se configuren correctamente.

2. **Limpieza**: Después de las pruebas, considera eliminar los recursos creados para mantener la base de datos limpia.

3. **Variables**: Asegúrate de que todas las variables estén configuradas antes de ejecutar cada prueba.

4. **Autenticación**: El token de autenticación expira, por lo que puede ser necesario hacer login nuevamente durante las pruebas largas.

5. **Cloud Storage**: Las pruebas de subida/descarga requieren configuración válida de S3 o GCS.

## Solución de Problemas

### Error 401 Unauthorized
- Verifica que el token de autenticación sea válido
- Haz login nuevamente si es necesario

### Error 400 Bad Request
- Verifica que todos los campos requeridos estén presentes
- Verifica que los IDs sean válidos (UUIDs)
- Verifica que los tipos MIME estén permitidos

### Error 404 Not Found
- Verifica que el recurso exista en la base de datos
- Verifica que el usuario tenga permisos para acceder al recurso

### Error 500 Internal Server Error
- Verifica la configuración del servidor
- Verifica los logs del servidor para más detalles
- Verifica la configuración de cloud storage
