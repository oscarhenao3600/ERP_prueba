#!/usr/bin/env python
"""
Script de diagnóstico para el sistema ERP.
"""

import os
import sys
import subprocess

def verificar_python():
    """Verificar que Python esté instalado."""
    print("🐍 Verificando Python...")
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"   ✅ Python: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def verificar_dependencias():
    """Verificar dependencias de Python."""
    print("📦 Verificando dependencias...")
    
    dependencias = [
        'django',
        'djangorestframework',
        'psycopg2',
        'django-cors-headers',
        'boto3',
        'python-decouple',
        'Pillow'
    ]
    
    faltantes = []
    
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - NO INSTALADO")
            faltantes.append(dep)
    
    if faltantes:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(faltantes)}")
        print("   Instalar con: pip install -r requirements.txt")
        return False
    
    return True

def verificar_postgresql():
    """Verificar conexión a PostgreSQL."""
    print("🗄️  Verificando PostgreSQL...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='postgres123',
            database='postgres'
        )
        conn.close()
        print("   ✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        print(f"   ❌ Error conectando a PostgreSQL: {e}")
        print("   💡 Soluciones:")
        print("     1. Instalar PostgreSQL: https://www.postgresql.org/download/windows/")
        print("     2. O usar Docker: docker run --name postgres-erp -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 -d postgres:15")
        print("     3. Verificar que el servicio esté ejecutándose")
        return False

def verificar_django():
    """Verificar configuración de Django."""
    print("🔧 Verificando Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_documents.settings.development')
        import django
        django.setup()
        print("   ✅ Django configurado correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error en Django: {e}")
        return False

def verificar_base_datos():
    """Verificar base de datos."""
    print("🗄️  Verificando base de datos...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("   ✅ Base de datos accesible")
                return True
    except Exception as e:
        print(f"   ❌ Error accediendo a la base de datos: {e}")
        return False

def crear_base_datos():
    """Crear base de datos si no existe."""
    print("🗄️  Creando base de datos...")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='postgres123',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE erp_documents;")
        cursor.close()
        conn.close()
        
        print("   ✅ Base de datos 'erp_documents' creada")
        return True
    except Exception as e:
        if "already exists" in str(e):
            print("   ℹ️  Base de datos 'erp_documents' ya existe")
            return True
        else:
            print(f"   ❌ Error creando base de datos: {e}")
            return False

def ejecutar_migraciones():
    """Ejecutar migraciones."""
    print("🔄 Ejecutando migraciones...")
    
    try:
        result = subprocess.run([sys.executable, 'manage.py', 'migrate'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Migraciones ejecutadas")
            return True
        else:
            print(f"   ❌ Error en migraciones: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error ejecutando migraciones: {e}")
        return False

def probar_servidor():
    """Probar que el servidor puede iniciar."""
    print("🚀 Probando servidor...")
    
    try:
        # Solo verificar que no hay errores de configuración
        result = subprocess.run([sys.executable, 'manage.py', 'check'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Configuración de Django correcta")
            return True
        else:
            print(f"   ❌ Error en configuración: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error verificando configuración: {e}")
        return False

def main():
    """Función principal de diagnóstico."""
    print("🔍 DIAGNÓSTICO DEL SISTEMA ERP")
    print("="*50)
    
    problemas = []
    
    # Verificaciones
    if not verificar_python():
        problemas.append("Python no está instalado")
    
    if not verificar_dependencias():
        problemas.append("Dependencias faltantes")
    
    if not verificar_postgresql():
        problemas.append("PostgreSQL no disponible")
    else:
        # Solo crear BD si PostgreSQL está disponible
        crear_base_datos()
    
    if not verificar_django():
        problemas.append("Error en configuración de Django")
    
    if not verificar_base_datos():
        problemas.append("Error accediendo a la base de datos")
    
    if not ejecutar_migraciones():
        problemas.append("Error en migraciones")
    
    if not probar_servidor():
        problemas.append("Error en configuración del servidor")
    
    print("\n" + "="*50)
    
    if problemas:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for i, problema in enumerate(problemas, 1):
            print(f"   {i}. {problema}")
        
        print("\n💡 SOLUCIONES RECOMENDADAS:")
        print("   1. Instalar PostgreSQL o usar Docker")
        print("   2. Ejecutar: pip install -r requirements.txt")
        print("   3. Verificar configuración en settings/development.py")
        print("   4. Ejecutar: python manage.py migrate")
        print("   5. Ejecutar: python manage.py runserver 8000")
        
        return False
    else:
        print("✅ SISTEMA LISTO")
        print("\n🚀 Próximos pasos:")
        print("   1. python manage.py runserver 8000")
        print("   2. Abrir http://localhost:8000")
        print("   3. Usar Postman para probar la API")
        
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
