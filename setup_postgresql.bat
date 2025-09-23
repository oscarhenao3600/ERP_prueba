@echo off
REM Script de configuración completa para PostgreSQL - Sistema ERP de gestión de documentos

echo 🚀 CONFIGURACIÓN COMPLETA DEL SISTEMA ERP CON POSTGRESQL
echo =========================================================

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado. Por favor instala Python 3.9 o superior.
    echo    Descarga desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar que pip está instalado
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip no está instalado. Por favor instala pip.
    pause
    exit /b 1
)

REM Crear directorio de logs
echo 📁 Creando directorio de logs...
if not exist logs mkdir logs

REM Crear directorio de media
echo 📁 Creando directorio de media...
if not exist media mkdir media

REM Crear directorio de static
echo 📁 Creando directorio de static...
if not exist static mkdir static

REM Crear directorio de simulación S3
echo 📁 Creando directorio de simulación S3...
if not exist s3_simulation mkdir s3_simulation
if not exist s3_simulation\companies mkdir s3_simulation\companies
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\vehicles mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\vehicles
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\employees mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\employees
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\equipment mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\equipment

REM Crear archivo .env si no existe
if not exist .env (
    echo 📝 Creando archivo .env...
    copy env_postgresql.txt .env
    echo ⚠️  Archivo .env creado. Verifica la configuración de PostgreSQL.
)

REM Instalar dependencias
echo 📦 Instalando dependencias de Python...
pip install -r requirements.txt

REM Verificar que PostgreSQL está disponible
echo 🗄️  Verificando conexión a PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL no está instalado. Por favor instala PostgreSQL 12 o superior.
    echo    Descarga desde: https://www.postgresql.org/download/windows/
    echo.
    echo    O usa Docker:
    echo    docker run --name postgres-erp -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 -d postgres:15
    echo.
    set /p response="¿Has configurado PostgreSQL? (y/n): "
    if /i not "%response%"=="y" (
        echo ❌ Por favor configura PostgreSQL y ejecuta este script nuevamente.
        pause
        exit /b 1
    )
)

REM Crear base de datos si no existe
echo 🗄️  Creando base de datos...
psql -U postgres -h localhost -c "CREATE DATABASE erp_documents;" 2>nul || echo ℹ️  Base de datos ya existe o error de conexión.

REM Ejecutar migraciones
echo 🔄 Ejecutando migraciones de Django...
python manage.py makemigrations
python manage.py migrate

REM Crear superusuario
echo 👤 Creando superusuario...
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>nul || echo ⚠️  Superusuario ya existe o hubo un error.

REM Ejecutar script de inicialización completa
echo 🧪 Ejecutando inicialización completa del sistema...
python init_postgresql_completo.py

REM Ejecutar pruebas
echo 🧪 Ejecutando pruebas unitarias...
python manage.py test

REM Generar reporte de coverage
echo 📊 Generando reporte de coverage...
coverage run --source=. manage.py test
coverage report
coverage html

echo ✅ Configuración completada exitosamente!
echo.
echo 🎉 El sistema ERP de gestión de documentos está listo para usar.
echo.
echo 📋 Próximos pasos:
echo    1. Ejecuta: python manage.py runserver 8000
echo    2. Accede a: http://localhost:8000/admin/
echo    3. Usa las credenciales: admin/admin (o las que configuraste)
echo    4. Importa la colección de Postman para probar la API
echo.
echo 📚 Documentación:
echo    - README.md: Documentación general del sistema
echo    - ERP_Documents_PostgreSQL.postman_collection.json: Colección de Postman
echo    - ERP_Documents_PostgreSQL.postman_environment.json: Entorno de Postman
echo.
echo 🔧 Comandos útiles:
echo    - python manage.py runserver: Iniciar servidor de desarrollo
echo    - python manage.py test: Ejecutar pruebas
echo    - python manage.py shell: Abrir shell de Django
echo    - python manage.py createsuperuser: Crear superusuario
echo.
echo ¡Disfruta usando el sistema! 🚀
pause
