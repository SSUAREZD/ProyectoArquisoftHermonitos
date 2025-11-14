from django.urls import path
from core.views import bodega_views, producto_views, inventario_views

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
    
    #------ Endpoints Inventario------
    path("inventario/", inventario_views.inventario_list, name="inventario_list"),
    path("inventario/create/", inventario_views.inventario_create, name="inventario_create"),

    # Detail + update + delete
    path("inventario/detail/", inventario_views.inventario_detail, name="inventario_detail"),
    path("inventario/update/", inventario_views.inventario_update, name="inventario_update"),
    path("inventario/delete/", inventario_views.inventario_delete, name="inventario_delete"),

    # Reservation operations
    path("inventario/reservar/", inventario_views.inventario_reservar, name="inventario_reservar"),
    path("inventario/liberar/", inventario_views.inventario_liberar_reserva, name="inventario_liberar_reserva"),
    path("inventario/confirmar/", inventario_views.inventario_confirmar_reserva, name="inventario_confirmar_reserva"),

    # Filters and queries
    path("inventario/bajo_stock/", inventario_views.inventario_bajo_stock, name="inventario_bajo_stock"),
    path("inventario/por_bodega/", inventario_views.inventario_por_bodega, name="inventario_por_bodega"),
    path("inventario/por_producto/", inventario_views.inventario_por_producto, name="inventario_por_producto"),
    path("inventario/disponibilidad/", inventario_views.inventario_disponibilidad_producto, name="inventario_disponibilidad_producto"),
    path("inventario/disponibilidad_bodega/", inventario_views.inventario_disponibilidad_bodega_producto, name="inventario_disponibilidad_bodega_producto"),
    path("inventario/total_stock/", inventario_views.inventario_total_stock, name="inventario_total_stock"),
    path("inventario/buscar/", inventario_views.inventario_buscar, name="inventario_buscar"),

    # Counts
    path("inventario/contar/", inventario_views.inventario_contar, name="inventario_contar"),
    path("inventario/contar_bodega/", inventario_views.inventario_contar_bodega, name="inventario_contar_bodega")
    ]