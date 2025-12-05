# inventario_service/inventario/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.services.inventario_service import InventarioService


@require_http_methods(["GET"])
def disponibilidad_producto(request):
    producto_id = request.GET.get("producto_id")
    bodega_id = request.GET.get("bodega_id", 1)

    result = InventarioService.obtener_disponibilidad(producto_id, bodega_id)
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def reservar_producto(request):
    producto_id = request.POST.get("producto_id")
    bodega_id = request.POST.get("bodega_id")
    cantidad = int(request.POST.get("cantidad", 0))

    result = InventarioService.reservar_producto(producto_id, bodega_id, cantidad)

    return JsonResponse(result, status=200 if result.get("success") else 400)
