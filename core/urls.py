from django.urls import path
from core.views import pedidos_views, checks

urlpatterns = [
    path('pedidos/', pedidos_views.pedidos_view, name='pedido_list'),
    path('pedidos/create/', pedidos_views.pedido_create, name='pedido_create'),
    path('pedidos/detail/', pedidos_views.pedido_detail, name='pedido_detail'),
    path('pedidos/update/', pedidos_views.pedido_update, name='pedido_update'),
    path('pedidos/delete/', pedidos_views.pedido_delete, name='pedido_delete'),
    path('api/inventario/check/', pedidos_views.check_inventory, name='check_inventory'),
]

