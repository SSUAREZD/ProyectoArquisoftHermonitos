from django.shortcuts import get_object_or_404
from core.models import (
    Pedido, Producto, ProductoPedido,
    Cliente, Direccion, CondicionPago, OrdenCompraCliente
)


class PedidoService:
    """Service for managing Pedido CRUD operations."""

    @staticmethod
    def crear_pedido(cliente_id, direccion_id, precio_calculado,
                     condicion_pago_id=None, orden_compra_id=None):
        """
        Crear un pedido SIN detalles inicialmente.
        Los detalles se crean luego (después de reservar inventario).
        """
        pedido = Pedido.objects.create(
            cliente_id=cliente_id,
            direccion_id=direccion_id,
            precio_calculado=precio_calculado,
            condicion_pago_id=condicion_pago_id,
            orden_compra_id=orden_compra_id
        )
        return pedido

    @staticmethod
    def agregar_item(pedido, producto_id, cantidad, precio_unitario):
        producto = Producto.objects.get(id=producto_id)
        return ProductoPedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=cantidad * precio_unitario
        )

    @staticmethod
    def obtener_pedido(pedido_id):
        return get_object_or_404(Pedido, id=pedido_id)

    @staticmethod
    def obtener_todos_pedidos():
        return Pedido.objects.all()

    @staticmethod
    def obtener_pedidos_por_cliente(cliente_id):
        return Pedido.objects.filter(cliente_id=cliente_id)

    @staticmethod
    def actualizar_pedido(pedido_id, **kwargs):
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

    @staticmethod
    def eliminar_pedido(pedido_id):
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.delete()
        return True

    @staticmethod
    def contar_pedidos():
        return Pedido.objects.count()