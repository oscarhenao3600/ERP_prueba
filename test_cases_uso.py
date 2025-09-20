#!/usr/bin/env python
"""
Script para ejecutar pruebas específicas de casos de uso del sistema ERP.

Este script ejecuta las pruebas de casos de uso de manera organizada,
mostrando resultados detallados y generando reportes específicos.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Configura Django para las pruebas."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_documents.settings.development')
    django.setup()

def run_test_suite():
    """Ejecuta la suite completa de pruebas de casos de uso."""
    print("🚀 Iniciando pruebas de casos de uso del sistema ERP...")
    print("=" * 60)
    
    # Configurar Django
    setup_django()
    
    # Configurar runner de pruebas
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Definir las pruebas a ejecutar
    test_suites = [
        'tests.test_cases_uso.DocumentUploadFlowTestCase',
        'tests.test_cases_uso.HierarchicalValidationTestCase',
        'tests.test_cases_uso.DocumentDownloadTestCase',
        'tests.test_cases_uso.DocumentManagementTestCase',
        'tests.test_cases_uso.ErrorHandlingTestCase',
    ]
    
    print("📋 Casos de uso a probar:")
    for i, suite in enumerate(test_suites, 1):
        print(f"   {i}. {suite.split('.')[-1]}")
    print()
    
    # Ejecutar cada suite de pruebas
    results = {}
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for suite in test_suites:
        print(f"🧪 Ejecutando: {suite.split('.')[-1]}")
        print("-" * 40)
        
        try:
            result = test_runner.run_tests([suite], verbosity=2)
            results[suite] = result
            
            # Extraer estadísticas
            if hasattr(result, 'testsRun'):
                total_tests += result.testsRun
            if hasattr(result, 'failures'):
                total_failures += len(result.failures)
            if hasattr(result, 'errors'):
                total_errors += len(result.errors)
                
        except Exception as e:
            print(f"❌ Error ejecutando {suite}: {e}")
            total_errors += 1
        
        print()
    
    # Mostrar resumen
    print("=" * 60)
    print("📊 RESUMEN DE PRUEBAS DE CASOS DE USO")
    print("=" * 60)
    print(f"Total de pruebas ejecutadas: {total_tests}")
    print(f"Fallos: {total_failures}")
    print(f"Errores: {total_errors}")
    print(f"Exitosas: {total_tests - total_failures - total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("✅ ¡Todas las pruebas de casos de uso pasaron exitosamente!")
        return True
    else:
        print("❌ Algunas pruebas fallaron. Revisa los detalles arriba.")
        return False

def run_specific_test_case(test_case_name):
    """Ejecuta un caso de prueba específico."""
    print(f"🎯 Ejecutando caso de prueba específico: {test_case_name}")
    print("=" * 60)
    
    # Configurar Django
    setup_django()
    
    # Configurar runner de pruebas
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Ejecutar prueba específica
    try:
        result = test_runner.run_tests([f'tests.test_cases_uso.{test_case_name}'], verbosity=2)
        
        print("=" * 60)
        print("📊 RESULTADO")
        print("=" * 60)
        
        if hasattr(result, 'testsRun'):
            print(f"Pruebas ejecutadas: {result.testsRun}")
        if hasattr(result, 'failures'):
            print(f"Fallos: {len(result.failures)}")
        if hasattr(result, 'errors'):
            print(f"Errores: {len(result.errors)}")
        
        if len(result.failures) == 0 and len(result.errors) == 0:
            print("✅ ¡Caso de prueba exitoso!")
            return True
        else:
            print("❌ Caso de prueba falló.")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando caso de prueba: {e}")
        return False

def run_test_method(test_case_name, test_method_name):
    """Ejecuta un método de prueba específico."""
    print(f"🔍 Ejecutando método específico: {test_case_name}.{test_method_name}")
    print("=" * 60)
    
    # Configurar Django
    setup_django()
    
    # Configurar runner de pruebas
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Ejecutar método específico
    test_path = f'tests.test_cases_uso.{test_case_name}.{test_method_name}'
    
    try:
        result = test_runner.run_tests([test_path], verbosity=2)
        
        print("=" * 60)
        print("📊 RESULTADO")
        print("=" * 60)
        
        if hasattr(result, 'testsRun'):
            print(f"Pruebas ejecutadas: {result.testsRun}")
        if hasattr(result, 'failures'):
            print(f"Fallos: {len(result.failures)}")
        if hasattr(result, 'errors'):
            print(f"Errores: {len(result.errors)}")
        
        if len(result.failures) == 0 and len(result.errors) == 0:
            print("✅ ¡Método de prueba exitoso!")
            return True
        else:
            print("❌ Método de prueba falló.")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando método de prueba: {e}")
        return False

def show_available_tests():
    """Muestra los casos de prueba disponibles."""
    print("📋 CASOS DE PRUEBA DISPONIBLES")
    print("=" * 60)
    
    test_cases = {
        'DocumentUploadFlowTestCase': {
            'description': 'Pruebas del flujo completo de subida de documentos',
            'methods': [
                'test_complete_upload_flow_with_validation',
                'test_upload_flow_without_validation',
                'test_upload_flow_invalid_data'
            ]
        },
        'HierarchicalValidationTestCase': {
            'description': 'Pruebas de validación jerárquica de documentos',
            'methods': [
                'test_hierarchical_approval_flow',
                'test_terminal_rejection_flow',
                'test_approval_permissions'
            ]
        },
        'DocumentDownloadTestCase': {
            'description': 'Pruebas de descarga de documentos',
            'methods': [
                'test_successful_download',
                'test_download_file_not_found',
                'test_download_storage_error',
                'test_download_unauthorized_access'
            ]
        },
        'DocumentManagementTestCase': {
            'description': 'Pruebas de gestión de documentos',
            'methods': [
                'test_list_documents',
                'test_get_document_details',
                'test_get_validation_status',
                'test_get_pending_approvals',
                'test_get_approval_stats',
                'test_delete_document'
            ]
        },
        'ErrorHandlingTestCase': {
            'description': 'Pruebas de manejo de errores',
            'methods': [
                'test_invalid_json_format',
                'test_missing_required_fields',
                'test_invalid_uuid_format',
                'test_nonexistent_resource',
                'test_unauthorized_access',
                'test_method_not_allowed'
            ]
        }
    }
    
    for case_name, info in test_cases.items():
        print(f"\n🔹 {case_name}")
        print(f"   Descripción: {info['description']}")
        print(f"   Métodos:")
        for method in info['methods']:
            print(f"      - {method}")
    
    print("\n" + "=" * 60)
    print("💡 COMANDOS DISPONIBLES:")
    print("   python test_cases_uso.py                    # Ejecutar todas las pruebas")
    print("   python test_cases_uso.py --show             # Mostrar casos disponibles")
    print("   python test_cases_uso.py --case CASE_NAME   # Ejecutar caso específico")
    print("   python test_cases_uso.py --method CASE.METHOD # Ejecutar método específico")

def main():
    """Función principal del script."""
    if len(sys.argv) == 1:
        # Ejecutar todas las pruebas
        success = run_test_suite()
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) == 2:
        if sys.argv[1] == '--show':
            show_available_tests()
        else:
            print("❌ Argumento no reconocido. Usa --show para ver opciones disponibles.")
            sys.exit(1)
    
    elif len(sys.argv) == 3:
        if sys.argv[1] == '--case':
            success = run_specific_test_case(sys.argv[2])
            sys.exit(0 if success else 1)
        else:
            print("❌ Argumento no reconocido.")
            sys.exit(1)
    
    elif len(sys.argv) == 4:
        if sys.argv[1] == '--method':
            case_name = sys.argv[2]
            method_name = sys.argv[3]
            success = run_test_method(case_name, method_name)
            sys.exit(0 if success else 1)
        else:
            print("❌ Argumento no reconocido.")
            sys.exit(1)
    
    else:
        print("❌ Número incorrecto de argumentos.")
        print("💡 Usa --show para ver las opciones disponibles.")
        sys.exit(1)

if __name__ == '__main__':
    main()
