from django.urls import path
from core.views import pedido_views, checks

urlpatterns = [
    path('pedidos/', pedido_views.pedidos_view, name='pedido_list'),
    path('pedidos/create/', pedido_views.pedido_create, name='pedido_create'),
    path('pedidos/detail/', pedido_views.pedido_detail, name='pedido_detail'),
    path('pedidos/update/', pedido_views.pedido_update, name='pedido_update'),
    path('pedidos/delete/', pedido_views.pedido_delete, name='pedido_delete'),
    path('api/inventario/check/', pedido_views.check_inventory, name='check_inventory'),
]

