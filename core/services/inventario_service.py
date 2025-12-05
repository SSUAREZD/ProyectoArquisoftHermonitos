from django.db import transaction
from ..models import Inventario

class InventarioService:

    @staticmethod
    def obtener_disponibilidad(producto_id, bodega_id):
        inv = Inventario.objects.filter(
            producto_id=producto_id,
            bodega_id=bodega_id
        ).first()

        if not inv:
            return {"disponible": False, "cantidad": 0}

        return {
            "disponible": inv.cantidad_disponible > 0,
            "cantidad": inv.cantidad_disponible
        }

    @staticmethod
    @transaction.atomic
    def reservar_producto(producto_id, bodega_id, cantidad):
        """
        Reserva stock en una transacción ACID.
        """
        inv = Inventario.objects.select_for_update().filter(
            producto_id=producto_id,
            bodega_id=bodega_id
        ).first()

        if not inv:
            return {"success": False, "error": "SIN_REGISTRO_INVENTARIO"}

        if inv.cantidad_disponible < cantidad:
            return {
                "success": False,
                "error": "STOCK_INSUFICIENTE",
                "disponible": inv.cantidad_disponible,
                "solicitado": cantidad,
            }

        inv.cantidad_disponible -= cantidad
        inv.cantidad_reservada += cantidad
        inv.save()

        return {
            "success": True,
            "producto_id": producto_id,
            "cantidad_reservada": cantidad
        }
