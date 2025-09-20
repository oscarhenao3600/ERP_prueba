"""
URLs para la aplicación de empresas.

Este módulo define las rutas URL para la API de gestión de empresas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CompanyViewSet, EntityViewSet, EntityTypeViewSet, UserViewSet

# Crear router para ViewSets
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'entity-types', EntityTypeViewSet, basename='entitytype')
router.register(r'users', UserViewSet, basename='user')

# URLs de la aplicación
urlpatterns = [
    path('', include(router.urls)),
]
