from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import Pedido, EstadoPedido

from django.shortcuts import get_object_or_404
from core.models import (
    Pedido, Producto, ProductoPedido, EstadoPedido,
    Cliente, Direccion, CondicionPago, OrdenCompraCliente
)


class PedidoService:
    """Service for managing Pedido CRUD operations."""

    # ---------------------------------------------------------
    # CREATE PEDIDO (with optional line items)
    # ---------------------------------------------------------
    @staticmethod
    def crear_pedido(cliente_id, direccion_id, precio_calculado,
                     condicion_pago_id=None, orden_compra_id=None,
                     detalles=None):
        """
        Crear un pedido con detalles opcionales.
        
        detalles = [
            {"producto_id": 1, "cantidad": 3, "precio_unitario": 10.0},
            ...
        ]
        """

        # Create main Pedido
        pedido = Pedido.objects.create(
            cliente_id=cliente_id,
            direccion_id=direccion_id,
            precio_calculado=precio_calculado,
            condicion_pago_id=condicion_pago_id,
            orden_compra_id=orden_compra_id
        )

        # Create ProductoPedido items
        if detalles:
            for item in detalles:
                ProductoPedido.objects.create(
                    pedido=pedido,
                    producto_id=item["producto_id"],
                    cantidad=item["cantidad"],
                    precio_unitario=item["precio_unitario"],
                    subtotal=item["cantidad"] * item["precio_unitario"]
                )

        return pedido

    # ---------------------------------------------------------
    # GET A SINGLE PEDIDO
    # ---------------------------------------------------------
    @staticmethod
    def obtener_pedido(pedido_id):
        return get_object_or_404(Pedido, id=pedido_id)

    # ---------------------------------------------------------
    # GET ALL PEDIDOS
    # ---------------------------------------------------------
    @staticmethod
    def obtener_todos_pedidos():
        return Pedido.objects.all()

    # ---------------------------------------------------------
    # GET PEDIDOS BY CLIENTE
    # ---------------------------------------------------------
    @staticmethod
    def obtener_pedidos_por_cliente(cliente_id):
        return Pedido.objects.filter(cliente_id=cliente_id)

    # ---------------------------------------------------------
    # GET PEDIDOS BY ESTADO (using EstadoPedido model)
    # ---------------------------------------------------------
    @staticmethod
    def obtener_pedidos_por_estado(nombre_estado):
        """
        Return pedidos that currently have a specific estado.
        A pedido may have multiple estados in its historial.
        """
        return Pedido.objects.filter(historial__nombre=nombre_estado).distinct()

    # ---------------------------------------------------------
    # UPDATE PEDIDO (valid fields only)
    # ---------------------------------------------------------
    @staticmethod
    def actualizar_pedido(pedido_id, **kwargs):
        """
        Allowed updates:
        - precio_calculado
        - cliente_id
        - direccion_id
        - condicion_pago_id
        - orden_compra_id
        """

        allowed_fields = {
            "precio_calculado",
            "cliente_id",
            "direccion_id",
            "condicion_pago_id",
            "orden_compra_id",
        }

        pedido = get_object_or_404(Pedido, id=pedido_id)

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(pedido, key, value)

        pedido.save()
        return pedido

    # ---------------------------------------------------------
    # DELETE PEDIDO
    # ---------------------------------------------------------
    @staticmethod
    def eliminar_pedido(pedido_id):
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.delete()
        return True

    # ---------------------------------------------------------
    # FILTER BY PRICE RANGE
    # ---------------------------------------------------------
    @staticmethod
    def obtener_pedidos_por_rango_precio(precio_min, precio_max):
        return Pedido.objects.filter(
            precio_calculado__gte=precio_min,
            precio_calculado__lte=precio_max
        )

    # ---------------------------------------------------------
    # COUNT PEDIDOS
    # ---------------------------------------------------------
    @staticmethod
    def contar_pedidos():
        return Pedido.objects.count()