import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.services.pedido_service import PedidoService
from core.services.inventario_client import InventarioClient
from core.models import Cliente, Direccion, Producto, ProductoPedido


# pedidos_service/core/views/pedido_views.py
@csrf_exempt
@require_http_methods(["POST"])
def pedido_create(request):
    try:
        cliente_id = request.POST.get('cliente_id')
        direccion_id = request.POST.get('direccion_id')
        precio_calculado = request.POST.get('precio_calculado')
        productos_str = request.POST.get('productos', '[]')
        bodega_id = request.POST.get('bodega_id', 1)

        productos = json.loads(productos_str)

        # 1) Crear pedido base
        pedido = PedidoService.crear_pedido(
            cliente_id=cliente_id,
            direccion_id=direccion_id,
            precio_calculado=precio_calculado
        )

        # 2) Reservar inventario en microservicio de inventario
        for item in productos:
            producto_id = item["producto_id"]
            cantidad = int(item["cantidad"])
            precio_unitario = float(item.get("precio_unitario", 0))

            reserva = InventarioClient.reservar_producto(
                producto_id, cantidad, bodega_id
            )

            if not reserva.get("success", False):
                pedido.delete()
                return JsonResponse({
                    "success": False,
                    "error": f"No se pudo reservar producto {producto_id}: {reserva.get('error')}"
                }, status=400)

            PedidoService.agregar_item(
                pedido=pedido,
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )

        return JsonResponse({"success": True, "pedido_id": pedido.id})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)