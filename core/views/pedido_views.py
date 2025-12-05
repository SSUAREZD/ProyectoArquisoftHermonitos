import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.services.pedido_service import PedidoService
from core.services.inventario_client import InventarioClient
from core.models import Pedido, Cliente, Direccion, Producto, ProductoPedido


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
    
def _serialize_pedido(pedido):
    """
    Convierte un Pedido en un dict JSON-friendly, incluyendo sus items.
    """
    return {
        "id": pedido.id,
        "cliente_id": pedido.cliente_id,
        "direccion_id": pedido.direccion_id,
        "precio_calculado": float(pedido.precio_calculado),
        "condicion_pago_id": pedido.condicion_pago_id,
        "orden_compra_id": pedido.orden_compra_id,
        "items": [
            {
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "precio_unitario": float(item.precio_unitario),
                "subtotal": float(item.subtotal),
            }
            for item in pedido.items.all()
        ],
    }

@require_http_methods(["GET"])
def pedidos_view(request):
    """
    Lista todos los pedidos (en JSON).
    Puedes filtrar por ?cliente_id=123 si quieres.
    """
    cliente_id = request.GET.get("cliente_id")

    if cliente_id:
        pedidos = PedidoService.obtener_pedidos_por_cliente(cliente_id)
    else:
        pedidos = PedidoService.obtener_todos_pedidos()

    data = [_serialize_pedido(p) for p in pedidos]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def pedido_detail(request):
    """
    Retorna el detalle de un pedido dado su id (?id=XX).
    """
    pedido_id = request.GET.get("id")
    if not pedido_id:
        return JsonResponse(
            {"error": "Parámetro 'id' es requerido"}, status=400
        )

    try:
        pedido = PedidoService.obtener_pedido(pedido_id)
        return JsonResponse(_serialize_pedido(pedido))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)

@require_http_methods(["GET"])
def check_inventory(request):
    """
    Proxy: consulta disponibilidad de un producto llamando al microservicio de inventario.
    Usa InventarioClient.consultar_disponibilidad.
    """
    producto_id = request.GET.get("producto_id")
    bodega_id = request.GET.get("bodega_id", 1)

    if not producto_id:
        return JsonResponse(
            {"error": "Parámetro 'producto_id' es requerido"}, status=400
        )

    try:
        result = InventarioClient.consultar_disponibilidad(
            producto_id=producto_id,
            bodega_id=bodega_id,
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse(
            {"error": f"Error consultando inventario: {str(e)}"},
            status=500,
        )
