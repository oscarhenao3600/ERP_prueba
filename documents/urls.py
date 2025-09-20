"""
URLs para la aplicación de documentos.

Este módulo define las rutas URL para la API de gestión de documentos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet

# Crear router para ViewSets
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

# URLs de la aplicación
urlpatterns = [
    path('', include(router.urls)),
]
