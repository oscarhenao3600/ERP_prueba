# 🔐 SEGURIDAD Y TRANSACCIONES - ERP DOCUMENTS

## 🛡️ Configuración de Seguridad

### 🔑 Variables de Entorno (.env)
```bash
# Configuración de Seguridad
SECRET_KEY=your-super-secret-key-here-change-in-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Base de Datos
DATABASE_URL=postgresql://user:password@localhost:5432/erp_documents

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Configuración de URLs Pre-firmadas
PRESIGNED_URL_EXPIRATION=3600
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 🔒 Configuración de Django
```python
# erp_documents/settings/base.py

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', 
                      cast=lambda v: [s.strip() for s in v.split(',')])

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'companies.User'

# Configuración de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS en producción
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

## 🔐 Autenticación y Autorización

### 🎫 Token Authentication
```python
# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}
```

### 👤 Permisos de Usuario
```python
# companies/models.py
class User(AbstractUser):
    """Modelo de usuario personalizado con permisos específicos."""
    
    def can_approve_documents(self):
        """Verifica si el usuario puede aprobar documentos."""
        return (
            self.is_active and 
            self.company.is_active and
            (self.is_staff or self.is_superuser or self.is_company_admin)
        )
    
    def can_access_document(self, document):
        """Verifica si el usuario puede acceder a un documento."""
        return (
            self.is_active and
            self.company == document.company and
            (self.is_staff or self.is_superuser or self.is_company_admin)
        )
```

## 🔄 Transacciones Atómicas

### 📄 Creación de Documento con Transacción
```python
# documents/views.py
@transaction.atomic
def create(self, request, *args, **kwargs):
    """
    Crea un nuevo documento con transacción atómica.
    
    Garantiza que:
    1. El documento se crea en la BD
    2. El flujo de validación se configura
    3. Si algo falla, todo se revierte
    """
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        with transaction.atomic():
            # Crear el documento
            document = Document.objects.create(
                company=company,
                entity=entity,
                name=document_data['name'],
                mime_type=document_data['mime_type'],
                size_bytes=document_data['size_bytes'],
                bucket_key=document_data['bucket_key'],
                file_hash=document_data.get('file_hash', ''),
                description=document_data.get('description', ''),
                created_by=request.user
            )
            
            # Crear flujo de validación si se proporciona
            validation_flow_data = serializer.validated_data.get('validation_flow')
            if validation_flow_data and validation_flow_data.get('enabled', False):
                ValidationService.create_validation_flow(
                    document, validation_flow_data['steps']
                )
            
            return Response(
                DocumentSerializer(document).data,
                status=status.HTTP_201_CREATED
            )
    
    except Exception as e:
        # La transacción se revierte automáticamente
        logger.error(f"Error al crear documento: {e}")
        return Response(
            {"error": "Error interno del servidor"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### ✅ Aprobación con Transacción
```python
# documents/validation_service.py
@staticmethod
def approve_document(document: Document, actor: User, reason: str = "") -> dict:
    """
    Aprueba un documento con transacción atómica.
    
    Garantiza que:
    1. Todos los pasos se actualizan correctamente
    2. Las acciones se registran
    3. El documento se marca como aprobado
    4. Si algo falla, todo se revierte
    """
    with transaction.atomic():
        # Encontrar pasos a aprobar
        steps_to_approve = document.validation_flow.steps.filter(
            order__lte=max_actor_order,
            status='P'
        )
        
        approved_steps = []
        
        # Aprobar todos los pasos hasta el orden del actor
        for step in steps_to_approve:
            step.status = 'A'
            step.save()
            
            # Crear acción de validación
            ValidationAction.objects.create(
                document=document,
                validation_step=step,
                actor=actor,
                action='A',
                reason=reason
            )
            
            approved_steps.append(step.order)
        
        # Verificar si es aprobación completa
        if is_fully_approved:
            document.validation_status = 'A'
            document.save()
        
        return {
            'approved_steps': approved_steps,
            'is_fully_approved': is_fully_approved,
            'validation_status': document.validation_status
        }
```

## 🔒 Validaciones de Seguridad

### 📁 Validación de Archivos
```python
# documents/services.py
class CloudStorageService:
    """Servicio base para operaciones de almacenamiento en la nube."""
    
    def validate_file(self, mime_type: str, size_bytes: int) -> None:
        """
        Valida el tipo MIME y el tamaño del archivo.
        
        Args:
            mime_type: Tipo MIME del archivo
            size_bytes: Tamaño del archivo en bytes
            
        Raises:
            ValidationError: Si el archivo no cumple los requisitos
        """
        # Validar tipo MIME
        if mime_type not in self.allowed_mime_types:
            raise ValidationError(
                f"Tipo MIME '{mime_type}' no permitido. "
                f"Tipos permitidos: {', '.join(self.allowed_mime_types)}"
            )
        
        # Validar tamaño
        if size_bytes <= 0:
            raise ValidationError("El tamaño del archivo debe ser mayor a cero.")
        
        if size_bytes > self.max_file_size:
            raise ValidationError(
                f"El archivo excede el tamaño máximo permitido "
                f"({self.max_file_size / (1024*1024):.2f} MB)."
            )
```

### 🏢 Validación de Empresa
```python
# documents/views.py
def get_queryset(self):
    """Retorna solo los documentos de la empresa del usuario autenticado."""
    user = self.request.user
    
    # Verificar que el usuario está activo
    if not user.is_active:
        return Document.objects.none()
    
    # Verificar que la empresa está activa
    if not user.company.is_active:
        return Document.objects.none()
    
    # Retornar solo documentos de la empresa del usuario
    return Document.objects.filter(
        company=user.company
    ).select_related(
        'company', 'entity', 'created_by', 'validation_flow'
    ).prefetch_related('validation_flow__steps__approver')
```

## 🔐 Políticas de AWS S3

### 🪣 Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyPublicAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalServiceName": [
            "your-application-service"
          ]
        }
      }
    },
    {
      "Sid": "AllowPreSignedURLs",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::your-account:role/your-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*",
      "Condition": {
        "StringLike": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

### 🔑 IAM Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name"
    }
  ]
}
```

## 🛡️ Middleware de Seguridad

### 🔒 Custom Security Middleware
```python
# middleware/security.py
class SecurityMiddleware:
    """
    Middleware personalizado para validaciones de seguridad adicionales.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Validar origen de la request
        if not self._is_valid_origin(request):
            return HttpResponseForbidden("Origen no autorizado")
        
        # Validar tamaño de request
        if not self._is_valid_request_size(request):
            return HttpResponseForbidden("Request demasiado grande")
        
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def _is_valid_origin(self, request):
        """Valida el origen de la request."""
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            allowed_origins = settings.CORS_ALLOWED_ORIGINS
            return origin in allowed_origins
        return True
    
    def _is_valid_request_size(self, request):
        """Valida el tamaño de la request."""
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            max_size = 10 * 1024 * 1024  # 10MB
            return int(content_length) <= max_size
        return True
```

## 📊 Logging de Seguridad

### 📝 Configuración de Logs
```python
# erp_documents/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': 'SECURITY {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'documents.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 🔍 Logging de Acciones
```python
# documents/views.py
import logging

security_logger = logging.getLogger('documents.security')

class DocumentViewSet(viewsets.ModelViewSet):
    def approve(self, request, pk=None):
        """Aprueba un documento con logging de seguridad."""
        document = self.get_object()
        
        # Log de intento de aprobación
        security_logger.info(
            f"Intento de aprobación - Documento: {document.id}, "
            f"Usuario: {request.user.username}, "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )
        
        try:
            # Lógica de aprobación
            result = ValidationService.approve_document(
                document, actor, reason
            )
            
            # Log de aprobación exitosa
            security_logger.info(
                f"Aprobación exitosa - Documento: {document.id}, "
                f"Usuario: {request.user.username}, "
                f"Pasos aprobados: {result['approved_steps']}"
            )
            
            return Response(result)
            
        except ValidationError as e:
            # Log de error de validación
            security_logger.warning(
                f"Error de validación en aprobación - Documento: {document.id}, "
                f"Usuario: {request.user.username}, "
                f"Error: {str(e)}"
            )
            raise
```

## 🔐 Encriptación de Datos Sensibles

### 🔑 Encriptación de Archivos
```python
# documents/services.py
import boto3
from botocore.exceptions import ClientError

class S3StorageService(CloudStorageService):
    """Servicio para operaciones con AWS S3."""
    
    def generate_presigned_upload_url(self, bucket_key: str, mime_type: str) -> Dict[str, Any]:
        """Genera una URL pre-firmada con encriptación."""
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': bucket_key,
                    'ContentType': mime_type,
                    'ServerSideEncryption': 'AES256',  # Encriptación del lado del servidor
                    'Metadata': {
                        'uploaded-by': 'erp-documents',
                        'encrypted': 'true'
                    }
                },
                ExpiresIn=self.url_expiration,
                HttpMethod='PUT'
            )
            
            return {
                'url': url,
                'fields': {
                    'Content-Type': mime_type,
                    'x-amz-server-side-encryption': 'AES256'
                }
            }
            
        except ClientError as e:
            logger.error(f"Error al generar URL de subida: {e}")
            raise ValidationError("Error al generar URL de subida")
```

## 🛡️ Validación de Integridad

### 🔍 Verificación de Hash
```python
# documents/models.py
import hashlib

class Document(models.Model):
    """Modelo de documento con verificación de integridad."""
    
    def verify_file_integrity(self, file_content: bytes) -> bool:
        """
        Verifica la integridad del archivo usando hash SHA-256.
        
        Args:
            file_content: Contenido del archivo en bytes
            
        Returns:
            True si el hash coincide, False en caso contrario
        """
        if not self.file_hash:
            return True  # No hay hash para verificar
        
        calculated_hash = hashlib.sha256(file_content).hexdigest()
        return calculated_hash == self.file_hash
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        Calcula el hash SHA-256 del archivo.
        
        Args:
            file_content: Contenido del archivo en bytes
            
        Returns:
            Hash SHA-256 en formato hexadecimal
        """
        return hashlib.sha256(file_content).hexdigest()
```

## 📋 Resumen de Seguridad

### ✅ Implementado
- ✅ Autenticación por tokens
- ✅ Autorización por empresa
- ✅ Validación de archivos
- ✅ Transacciones atómicas
- ✅ Logging de seguridad
- ✅ Headers de seguridad
- ✅ Encriptación S3
- ✅ Verificación de integridad

### 🔒 Buenas Prácticas
- 🔐 Credenciales en variables de entorno
- 🔐 Políticas IAM restrictivas
- 🔐 URLs pre-firmadas con expiración
- 🔐 Validación de entrada estricta
- 🔐 Logging de todas las acciones
- 🔐 Transacciones para consistencia
- 🔐 Encriptación en tránsito y reposo
