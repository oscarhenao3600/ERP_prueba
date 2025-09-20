#!/bin/bash
# Script para ejecutar pruebas de casos de uso del sistema ERP

echo "🧪 Ejecutando pruebas de casos de uso del sistema ERP de gestión de documentos..."
echo "=================================================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Asegúrate de estar en el directorio del proyecto."
    exit 1
fi

# Verificar que Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado."
    exit 1
fi

echo "📋 Ejecutando pruebas de casos de uso..."
echo ""

# Ejecutar pruebas específicas de casos de uso
echo "🔹 Pruebas de flujo de subida de documentos..."
python3 manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase -v 2

echo ""
echo "🔹 Pruebas de validación jerárquica..."
python3 manage.py test tests.test_cases_uso.HierarchicalValidationTestCase -v 2

echo ""
echo "🔹 Pruebas de descarga de documentos..."
python3 manage.py test tests.test_cases_uso.DocumentDownloadTestCase -v 2

echo ""
echo "🔹 Pruebas de gestión de documentos..."
python3 manage.py test tests.test_cases_uso.DocumentManagementTestCase -v 2

echo ""
echo "🔹 Pruebas de manejo de errores..."
python3 manage.py test tests.test_cases_uso.ErrorHandlingTestCase -v 2

echo ""
echo "=================================================================================="
echo "✅ Pruebas de casos de uso completadas!"
echo ""
echo "💡 Para ejecutar pruebas específicas:"
echo "   python3 manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase"
echo "   python3 manage.py test tests.test_cases_uso.HierarchicalValidationTestCase"
echo "   python3 manage.py test tests.test_cases_uso.DocumentDownloadTestCase"
echo "   python3 manage.py test tests.test_cases_uso.DocumentManagementTestCase"
echo "   python3 manage.py test tests.test_cases_uso.ErrorHandlingTestCase"
echo ""
echo "💡 Para ejecutar un método específico:"
echo "   python3 manage.py test tests.test_cases_uso.DocumentUploadFlowTestCase.test_complete_upload_flow_with_validation"
echo ""
echo "💡 Para ejecutar todas las pruebas del sistema:"
echo "   python3 manage.py test"
echo ""
echo "🎉 ¡Sistema listo para usar!"
