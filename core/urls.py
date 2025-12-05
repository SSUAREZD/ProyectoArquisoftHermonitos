from django.contrib import admin
from django.urls import path
from core.views import pedido_views, producto_views

urlpatterns = [
    # ===== PEDIDOS =====
    # Listar pedidos (HTML o JSON)
    path("api/pedidos/", pedido_views.pedidos_view, name="pedidos-list"),

    # Crear pedido (crea pedido + reserva inventario vía HTTP)
    path("api/pedidos/create/", pedido_views.pedido_create, name="pedido-create"),

    # Detalle de pedido por ?id=xx
    path("api/pedidos/detail/", pedido_views.pedido_detail, name="pedido-detail"),

    # Proxy para revisar inventario desde pedidos (usa InventarioClient)
    path(
        "api/pedidos/check-inventory/",
        pedido_views.check_inventory,
        name="pedido-check-inventory",
    ),

    # ===== PRODUCTOS (CATÁLOGO) =====
    path(
        "api/productos/",
        producto_views.productos_list_create_api,
        name="productos-list-create",
    ),
    path(
        "api/productos/<int:producto_id>/",
        producto_views.producto_detail_api,
        name="producto-detail",
    ),
]
