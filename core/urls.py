from django.contrib import admin
from django.urls import path
from core.views import pedido_views, producto_views

urlpatterns = [
    # ===== PEDIDOS =====
    # Listar pedidos (HTML o JSON)
    path("pedidos/", pedido_views.pedidos_view, name="pedidos-list"),

    # Crear pedido (crea pedido + reserva inventario vía HTTP)
    path("pedidos/create/", pedido_views.pedido_create, name="pedido-create"),

    # Detalle de pedido por ?id=xx
    path("pedidos/detail/", pedido_views.pedido_detail, name="pedido-detail"),

    # Proxy para revisar inventario desde pedidos (usa InventarioClient)
    path(
        "pedidos/check-inventory/",
        pedido_views.check_inventory,
        name="pedido-check-inventory",
    ),

    # ===== PRODUCTOS (CATÁLOGO) =====
    path(
        "productos/",
        producto_views.productos_list_create_api,
        name="productos-list-create",
    ),
    path(
        "productos/<int:producto_id>/",
        producto_views.producto_detail_api,
        name="producto-detail",
    ),
]
