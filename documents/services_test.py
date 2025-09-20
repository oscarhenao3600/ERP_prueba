"""
Servicios simplificados para pruebas locales del sistema ERP de gestión de documentos.

Este módulo contiene implementaciones mock de los servicios de cloud storage
para permitir la ejecución de pruebas sin dependencias externas.
"""

import uuid
import hashlib
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class MockCloudStorageService:
    """
    Servicio mock para operaciones de cloud storage.
    
    Implementa las operaciones de cloud storage usando almacenamiento simulado,
    útil para pruebas y desarrollo local.
    """
    
    def __init__(self):
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'test-bucket')
        self.url_expiration = getattr(settings, 'PRESIGNED_URL_EXPIRATION', 3600)
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10485760)  # 10MB
        allowed_mime_types_str = getattr(settings, 'ALLOWED_MIME_TYPES', 
            'application/pdf,image/jpeg,image/png,image/gif,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.allowed_mime_types = allowed_mime_types_str.split(',') if isinstance(allowed_mime_types_str, str) else allowed_mime_types_str
        
        # Simular almacenamiento en memoria
        self._storage = {}
        logger.info("Servicio mock de cloud storage inicializado")
    
    def validate_file(self, mime_type: str, size_bytes: int) -> None:
        """
        Valida el tipo MIME y tamaño del archivo.
        
        Args:
            mime_type: Tipo MIME del archivo
            size_bytes: Tamaño del archivo en bytes
            
        Raises:
            ValidationError: Si el archivo no es válido
        """
        if mime_type not in self.allowed_mime_types:
            raise ValidationError(f"Tipo MIME no permitido: {mime_type}")
        
        if size_bytes > self.max_file_size:
            raise ValidationError(f"Archivo demasiado grande: {size_bytes} bytes (máximo: {self.max_file_size})")
        
        if size_bytes <= 0:
            raise ValidationError("El tamaño del archivo debe ser mayor a 0")
    
    def generate_bucket_key(self, company_id: str, entity_type: str, entity_id: str, filename: str) -> str:
        """
        Genera una clave única para el archivo en el bucket.
        
        Args:
            company_id: ID de la empresa
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            filename: Nombre del archivo
            
        Returns:
            Clave única para el archivo en el bucket
        """
        # Generar hash único para evitar colisiones
        unique_id = str(uuid.uuid4())
        bucket_key = f"companies/{company_id}/{entity_type}/{entity_id}/{unique_id}_{filename}"
        
        logger.info(f"Clave de bucket generada: {bucket_key}")
        return bucket_key
    
    def generate_presigned_upload_url(self, bucket_key: str, mime_type: str) -> Dict[str, Any]:
        """
        Genera una URL pre-firmada simulada para subir un archivo.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            mime_type: Tipo MIME del archivo
            
        Returns:
            Dict con la URL simulada y campos necesarios
            
        Raises:
            ValidationError: Si hay error en la validación
        """
        try:
            # Simular URL pre-firmada
            upload_url = f"https://mock-storage.example.com/upload/{bucket_key}"
            
            logger.info(f"URL de subida simulada generada: {bucket_key}")
            
            return {
                'url': upload_url,
                'fields': {
                    'Content-Type': mime_type,
                    'bucket_key': bucket_key
                }
            }
            
        except Exception as e:
            logger.error(f"Error al generar URL de subida simulada: {e}")
            raise ValidationError(f"Error al generar URL de subida: {str(e)}")
    
    def generate_presigned_download_url(self, bucket_key: str) -> str:
        """
        Genera una URL pre-firmada simulada para descargar un archivo.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            URL simulada para descarga
            
        Raises:
            ValidationError: Si el archivo no existe
        """
        try:
            # Verificar que el archivo existe en el almacenamiento simulado
            if bucket_key not in self._storage:
                raise ValidationError("El archivo no existe en el bucket")
            
            # Simular URL pre-firmada
            download_url = f"https://mock-storage.example.com/download/{bucket_key}"
            
            logger.info(f"URL de descarga simulada generada: {bucket_key}")
            return download_url
            
        except Exception as e:
            logger.error(f"Error al generar URL de descarga simulada: {e}")
            raise ValidationError(f"Error al generar URL de descarga: {str(e)}")
    
    def delete_file(self, bucket_key: str) -> bool:
        """
        Elimina un archivo del almacenamiento simulado.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            if bucket_key in self._storage:
                del self._storage[bucket_key]
                logger.info(f"Archivo eliminado del almacenamiento simulado: {bucket_key}")
                return True
            else:
                logger.warning(f"Archivo no encontrado para eliminar: {bucket_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error al eliminar archivo del almacenamiento simulado: {e}")
            return False
    
    def file_exists(self, bucket_key: str) -> bool:
        """
        Verifica si un archivo existe en el almacenamiento simulado.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            exists = bucket_key in self._storage
            logger.debug(f"Verificación de existencia de archivo: {bucket_key} -> {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Error al verificar existencia de archivo: {e}")
            return False
    
    def get_file_metadata(self, bucket_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los metadatos de un archivo del almacenamiento simulado.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            Dict con los metadatos del archivo o None si no existe
        """
        try:
            if bucket_key not in self._storage:
                return None
            
            metadata = self._storage[bucket_key]
            logger.debug(f"Metadatos obtenidos para archivo: {bucket_key}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error al obtener metadatos del archivo: {e}")
            return None
    
    def store_file(self, bucket_key: str, metadata: Dict[str, Any]) -> bool:
        """
        Almacena metadatos de archivo en el almacenamiento simulado.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            metadata: Metadatos del archivo
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            self._storage[bucket_key] = metadata
            logger.info(f"Metadatos almacenados para archivo: {bucket_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error al almacenar metadatos del archivo: {e}")
            return False


# Instancia global del servicio mock
storage_service = MockCloudStorageService()
