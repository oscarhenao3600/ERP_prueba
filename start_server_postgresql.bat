@echo off
echo 🚀 INICIANDO SERVIDOR ERP DOCUMENTS (PostgreSQL)
echo ================================================

echo 📁 Verificando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Entorno virtual no encontrado. Ejecuta primero: python -m venv venv
    pause
    exit /b 1
)

echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

echo 🗄️ Verificando conexión a PostgreSQL...
python -c "import psycopg2; psycopg2.connect(host='localhost', database='erp_documents', user='postgres', password='oscar3600'); print('✅ Conexión a PostgreSQL exitosa')" 2>nul
if errorlevel 1 (
    echo ❌ Error de conexión a PostgreSQL. Verifica que esté ejecutándose.
    pause
    exit /b 1
)

echo 🌐 Iniciando servidor Django...
echo.
echo 📋 INFORMACIÓN DEL SISTEMA:
echo    Base de datos: PostgreSQL (erp_documents)
echo    Usuario: postgres
echo    Servidor: http://localhost:8000
echo    API Base: http://localhost:8000/api/
echo.
echo 🔑 CREDENCIALES DE PRUEBA:
echo    Sustentador: sustentador / sustentacion123
echo    Aprobador 1: aprobador1 / aprobador123
echo    Aprobador 2: aprobador2 / aprobador123
echo    Admin: admin / admin123
echo.
echo 📄 DOCUMENTOS DISPONIBLES:
echo    SOAT Vehículo: 05a7bcab-9015-4923-9bd3-ed54424d6fc7
echo    Contrato Laboral: b2c3d4e5-f6a7-8901-bcde-f23456789012
echo    Manual Equipo: c3d4e5f6-a7b8-9012-cdef-345678901234
echo.
echo 🚀 Iniciando servidor...
echo    Presiona Ctrl+C para detener el servidor
echo.

python manage.py runserver 8000

