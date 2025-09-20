"""
Servicios de cloud storage para el sistema ERP de gestión de documentos.

Este módulo contiene los servicios para interactuar con Amazon S3 y Google Cloud Storage,
incluyendo la generación de URLs pre-firmadas para subida y descarga de archivos.
"""

import os
import uuid
import hashlib
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.exceptions import ValidationError
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from google.cloud import storage as gcs
from google.cloud.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)


class CloudStorageService:
    """
    Servicio base para operaciones de cloud storage.
    
    Proporciona una interfaz común para diferentes proveedores de almacenamiento
    en la nube, permitiendo cambiar entre S3 y GCS sin afectar el código cliente.
    """
    
    def __init__(self):
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME
        self.expiration = settings.PRESIGNED_URL_EXPIRATION
    
    def generate_bucket_key(self, company_id: str, entity_type: str, entity_id: str, filename: str) -> str:
        """
        Genera una clave única para el archivo en el bucket.
        
        Args:
            company_id: ID de la empresa
            entity_type: Tipo de entidad (vehicle, employee, etc.)
            entity_id: ID de la entidad
            filename: Nombre del archivo
            
        Returns:
            Clave única para el archivo en el bucket
        """
        # Generar un UUID único para evitar colisiones
        unique_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        
        # Estructura: companies/{company_id}/{entity_type}/{entity_id}/docs/{unique_id}{extension}
        bucket_key = f"companies/{company_id}/{entity_type}/{entity_id}/docs/{unique_id}{file_extension}"
        
        return bucket_key
    
    def validate_file(self, file_data: bytes, mime_type: str, size_bytes: int) -> None:
        """
        Valida un archivo antes de subirlo.
        
        Args:
            file_data: Datos del archivo
            mime_type: Tipo MIME del archivo
            size_bytes: Tamaño del archivo en bytes
            
        Raises:
            ValidationError: Si el archivo no cumple con los requisitos
        """
        # Validar tamaño
        if size_bytes > settings.MAX_FILE_SIZE:
            raise ValidationError(f"El archivo excede el tamaño máximo permitido de {settings.MAX_FILE_SIZE} bytes")
        
        # Validar tipo MIME
        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise ValidationError(f"Tipo MIME '{mime_type}' no permitido")
        
        # Validar que el archivo no esté vacío
        if size_bytes == 0:
            raise ValidationError("El archivo no puede estar vacío")
    
    def calculate_file_hash(self, file_data: bytes) -> str:
        """
        Calcula el hash SHA-256 de un archivo.
        
        Args:
            file_data: Datos del archivo
            
        Returns:
            Hash SHA-256 del archivo
        """
        return hashlib.sha256(file_data).hexdigest()


class S3StorageService(CloudStorageService):
    """
    Servicio para operaciones con Amazon S3.
    
    Implementa las operaciones de cloud storage usando Amazon S3,
    incluyendo la generación de URLs pre-firmadas.
    """
    
    def __init__(self):
        super().__init__()
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region
            )
        except NoCredentialsError:
            logger.error("Credenciales de AWS no configuradas")
            raise
    
    def generate_presigned_upload_url(self, bucket_key: str, mime_type: str) -> Dict[str, Any]:
        """
        Genera una URL pre-firmada para subir un archivo a S3.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            mime_type: Tipo MIME del archivo
            
        Returns:
            Diccionario con la URL pre-firmada y campos adicionales
            
        Raises:
            ClientError: Si hay un error al generar la URL
        """
        try:
            # Configurar parámetros para la URL pre-firmada
            fields = {
                'Content-Type': mime_type,
            }
            
            conditions = [
                {'Content-Type': mime_type},
                ['content-length-range', 1, settings.MAX_FILE_SIZE]
            ]
            
            # Generar URL pre-firmada para POST (multipart upload)
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=bucket_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=self.expiration
            )
            
            logger.info(f"URL pre-firmada generada para subida: {bucket_key}")
            return response
            
        except ClientError as e:
            logger.error(f"Error al generar URL pre-firmada para subida: {e}")
            raise
    
    def generate_presigned_download_url(self, bucket_key: str) -> str:
        """
        Genera una URL pre-firmada para descargar un archivo de S3.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            URL pre-firmada para descarga
            
        Raises:
            ClientError: Si hay un error al generar la URL
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': bucket_key},
                ExpiresIn=self.expiration
            )
            
            logger.info(f"URL pre-firmada generada para descarga: {bucket_key}")
            return response
            
        except ClientError as e:
            logger.error(f"Error al generar URL pre-firmada para descarga: {e}")
            raise
    
    def file_exists(self, bucket_key: str) -> bool:
        """
        Verifica si un archivo existe en S3.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=bucket_key)
            return True
        except ClientError:
            return False
    
    def delete_file(self, bucket_key: str) -> bool:
        """
        Elimina un archivo de S3.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si el archivo fue eliminado exitosamente
            
        Raises:
            ClientError: Si hay un error al eliminar el archivo
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=bucket_key)
            logger.info(f"Archivo eliminado de S3: {bucket_key}")
            return True
        except ClientError as e:
            logger.error(f"Error al eliminar archivo de S3: {e}")
            raise
    
    def get_file_metadata(self, bucket_key: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de un archivo en S3.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            Diccionario con metadatos del archivo
            
        Raises:
            ClientError: Si hay un error al obtener metadatos
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=bucket_key)
            return {
                'size': response['ContentLength'],
                'mime_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'etag': response['ETag']
            }
        except ClientError as e:
            logger.error(f"Error al obtener metadatos del archivo: {e}")
            raise


class GCSStorageService(CloudStorageService):
    """
    Servicio para operaciones con Google Cloud Storage.
    
    Implementa las operaciones de cloud storage usando Google Cloud Storage,
    incluyendo la generación de URLs pre-firmadas.
    """
    
    def __init__(self):
        super().__init__()
        try:
            self.gcs_client = gcs.Client()
            self.bucket = self.gcs_client.bucket(self.bucket_name)
        except Exception as e:
            logger.error(f"Error al inicializar cliente GCS: {e}")
            raise
    
    def generate_presigned_upload_url(self, bucket_key: str, mime_type: str) -> Dict[str, Any]:
        """
        Genera una URL pre-firmada para subir un archivo a GCS.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            mime_type: Tipo MIME del archivo
            
        Returns:
            Diccionario con la URL pre-firmada y campos adicionales
        """
        try:
            blob = self.bucket.blob(bucket_key)
            
            # Generar URL pre-firmada para PUT
            url = blob.generate_signed_url(
                version="v4",
                expiration=self.expiration,
                method="PUT",
                content_type=mime_type
            )
            
            logger.info(f"URL pre-firmada generada para subida: {bucket_key}")
            return {
                'url': url,
                'fields': {
                    'Content-Type': mime_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error al generar URL pre-firmada para subida: {e}")
            raise
    
    def generate_presigned_download_url(self, bucket_key: str) -> str:
        """
        Genera una URL pre-firmada para descargar un archivo de GCS.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            URL pre-firmada para descarga
        """
        try:
            blob = self.bucket.blob(bucket_key)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=self.expiration,
                method="GET"
            )
            
            logger.info(f"URL pre-firmada generada para descarga: {bucket_key}")
            return url
            
        except Exception as e:
            logger.error(f"Error al generar URL pre-firmada para descarga: {e}")
            raise
    
    def file_exists(self, bucket_key: str) -> bool:
        """
        Verifica si un archivo existe en GCS.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            blob = self.bucket.blob(bucket_key)
            return blob.exists()
        except Exception:
            return False
    
    def delete_file(self, bucket_key: str) -> bool:
        """
        Elimina un archivo de GCS.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            True si el archivo fue eliminado exitosamente
        """
        try:
            blob = self.bucket.blob(bucket_key)
            blob.delete()
            logger.info(f"Archivo eliminado de GCS: {bucket_key}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar archivo de GCS: {e}")
            raise
    
    def get_file_metadata(self, bucket_key: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de un archivo en GCS.
        
        Args:
            bucket_key: Clave del archivo en el bucket
            
        Returns:
            Diccionario con metadatos del archivo
        """
        try:
            blob = self.bucket.blob(bucket_key)
            blob.reload()
            
            return {
                'size': blob.size,
                'mime_type': blob.content_type,
                'last_modified': blob.updated,
                'etag': blob.etag
            }
        except Exception as e:
            logger.error(f"Error al obtener metadatos del archivo: {e}")
            raise


def get_storage_service() -> CloudStorageService:
    """
    Factory function para obtener el servicio de storage apropiado.
    
    Returns:
        Instancia del servicio de storage configurado
    """
    # Por defecto usar S3, pero se puede cambiar según configuración
    if hasattr(settings, 'GOOGLE_CLOUD_PROJECT_ID'):
        return GCSStorageService()
    else:
        return S3StorageService()


# Instancia global del servicio de storage
storage_service = get_storage_service()
