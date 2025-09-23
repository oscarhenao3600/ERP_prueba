@echo off
echo 🚀 CONFIGURACIÓN COMPLETA CON POSTGRESQL
echo =========================================

echo 🗄️  Creando base de datos...
echo oscar3600 | psql -U postgres -h localhost -c "CREATE DATABASE erp_documents;" 2>nul || echo ℹ️  Base de datos ya existe

echo 📁 Creando directorios...
if not exist logs mkdir logs
if not exist staticfiles mkdir staticfiles
if not exist media mkdir media
if not exist s3_simulation mkdir s3_simulation
if not exist s3_simulation\companies mkdir s3_simulation\companies
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\vehicles mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\vehicles
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\employees mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\employees
if not exist s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\equipment mkdir s3_simulation\companies\fb36990a-7101-4f07-9b1f-c58bf492355b\equipment

echo 🔄 Ejecutando migraciones...
python manage.py makemigrations
python manage.py migrate

echo 🧪 Ejecutando inicialización completa...
python init_postgresql_completo.py

echo ✅ CONFIGURACIÓN COMPLETADA
echo =========================================
echo 🎉 El sistema ERP está listo para usar con PostgreSQL.
echo.
echo 🔑 CREDENCIALES:
echo    Sustentador: sustentador / sustentacion123
echo    Aprobador 1: aprobador1 / aprobador123
echo    Aprobador 2: aprobador2 / aprobador123
echo    Admin: admin / admin123
echo.
echo 🚀 PRÓXIMOS PASOS:
echo    1. python manage.py runserver 8000
echo    2. Abrir http://localhost:8000
echo    3. Importar colección Postman: ERP_Documents_PostgreSQL.postman_collection.json
echo    4. Importar entorno Postman: ERP_Documents_PostgreSQL.postman_environment.json
echo.
echo 📊 DATOS CREADOS:
echo    - Empresa: Empresa Sustentación Demo
echo    - Vehículo: Vehículo Demo (Toyota Yaris)
echo    - Empleado: Empleado Demo (Juan Pérez)
echo    - Equipo: Equipo Demo (Laptop Dell)
echo    - Documentos: SOAT, Contrato, Manual
echo.
pause
