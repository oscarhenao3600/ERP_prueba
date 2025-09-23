@echo off
echo 🔍 DIAGNÓSTICO DEL SISTEMA ERP
echo ================================

echo 🐍 Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python no está instalado
    pause
    exit /b 1
)

echo.
echo 📦 Verificando dependencias...
pip list | findstr django
if errorlevel 1 (
    echo ❌ Django no está instalado
    echo 💡 Instalar con: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo 🗄️  Verificando PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL no está instalado
    echo 💡 Instalar desde: https://www.postgresql.org/download/windows/
    echo 💡 O usar Docker: docker run --name postgres-erp -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 -d postgres:15
    pause
    exit /b 1
)

echo.
echo 🔧 Verificando configuración de Django...
python manage.py check
if errorlevel 1 (
    echo ❌ Error en configuración de Django
    pause
    exit /b 1
)

echo.
echo 🗄️  Creando base de datos...
psql -U postgres -h localhost -c "CREATE DATABASE erp_documents;" 2>nul || echo ℹ️  Base de datos ya existe

echo.
echo 🔄 Ejecutando migraciones...
python manage.py migrate
if errorlevel 1 (
    echo ❌ Error en migraciones
    pause
    exit /b 1
)

echo.
echo ✅ SISTEMA LISTO
echo ================================
echo 🚀 Próximos pasos:
echo    1. python manage.py runserver 8000
echo    2. Abrir http://localhost:8000
echo    3. Usar Postman para probar la API
echo.
pause
