from django.urls import path
from core.views.bodega_views import mapa_bodegas_view, dashboard_bodegas_view, bodegas_data_api

urlpatterns = [
    path('bodegas/mapa/', mapa_bodegas_view, name='mapa_bodegas'),
    path('bodegas/dashboard/', dashboard_bodegas_view, name='dashboard_bodegas'),
    path('api/bodegas/', bodegas_data_api, name='bodegas_data_api'),
]