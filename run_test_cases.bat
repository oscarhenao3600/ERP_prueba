@echo off
REM Script para ejecutar pruebas de casos de uso del sistema ERP (Windows)

echo 🧪 Ejecutando pruebas de casos de uso del sistema ERP de gestión de documentos...
echo ==================================================================================

REM Verificar que estamos en el directorio correcto
if not exist "manage.py" (
    echo ❌ Error: No se encontró manage.py. Asegúrate de estar en el directorio del proyecto.
    pause
    exit /b 1
)

REM Verificar que Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python no está instalado.
    pause
    exit /b 1
)

echo 📋 Ejecutando pruebas de casos de uso...
echo.

REM Ejecutar pruebas específicas de casos de uso
echo 🔹 Pruebas de flujo de subida de documentos...
python manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase -v 2

echo.
echo 🔹 Pruebas de validación jerárquica...
python manage.py test tests.test_cases_uso.HierarchicalValidationTestCase -v 2

echo.
echo 🔹 Pruebas de descarga de documentos...
python manage.py test tests.test_cases_uso.DocumentDownloadTestCase -v 2

echo.
echo 🔹 Pruebas de gestión de documentos...
python manage.py test tests.test_cases_uso.DocumentManagementTestCase -v 2

echo.
echo 🔹 Pruebas de manejo de errores...
python manage.py test tests.test_cases_uso.ErrorHandlingTestCase -v 2

echo.
echo ==================================================================================
echo ✅ Pruebas de casos de uso completadas!
echo.
echo 💡 Para ejecutar pruebas específicas:
echo    python manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase
echo    python manage.py test tests.test_cases_uso.HierarchicalValidationTestCase
echo    python manage.py test tests.test_cases_uso.DocumentDownloadTestCase
echo    python manage.py test tests.test_cases_uso.DocumentManagementTestCase
echo    python manage.py test tests.test_cases_uso.ErrorHandlingTestCase
echo.
echo 💡 Para ejecutar un método específico:
echo    python manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase.test_complete_upload_flow_with_validation
echo.
echo 💡 Para ejecutar todas las pruebas del sistema:
echo    python manage.py test
echo.
echo 🎉 ¡Sistema listo para usar!
pause
