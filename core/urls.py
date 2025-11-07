from django.urls import path
from core.views import bodega_views, producto_views

urlpatterns = [
    # Vistas HTML
    path('bodegas/mapa/', bodega_views.mapa_bodegas_view, name='mapa_bodegas'),
    path('bodegas/dashboard/', bodega_views.dashboard_bodegas_view, name='dashboard_bodegas'),

    # APIs existentes
    path('api/bodegas/', bodega_views.bodegas_data_api, name='bodegas_data_api'),

    # APIs nuevas para el dashboard
    path('api/kpis/', bodega_views.kpis_api, name='kpis_api'),
    path('api/mix-disponible-reservado/', bodega_views.mix_disponible_reservado_api, name='mix_disponible_reservado_api'),
    path('api/aging/', bodega_views.aging_api, name='aging_api'),
    path('api/top-skus/', bodega_views.top_skus_api, name='top_skus_api'),
    path('api/tareas-estado/', bodega_views.tareas_estado_api, name='tareas_estado_api'),

    # Endpoints CRUD para Producto
    path('api/productos/', producto_views.productos_list_create_api, name='productos_list_create_api'),
    path('api/productos/<int:producto_id>/', producto_views.producto_detail_api, name='producto_detail_api'),
]
