from django.urls import path
from core.views.inventario_views import (
    disponibilidad_producto,
    reservar_producto,
)

urlpatterns = [
    # consultar disponibilidad
    path("inventarios/disponibilidad/", disponibilidad_producto, name="inventario-disponibilidad"),

    # reservar producto
    path("inventarios/reservar/", reservar_producto, name="inventario-reservar"),
]
