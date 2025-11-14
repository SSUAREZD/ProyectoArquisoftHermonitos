from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import requests
from core.services.pedido_service import PedidoService
from core.services.checks_service import ChecksService
from core.models import Cliente, Direccion, Producto, Inventario, ProductoPedido
from django.conf import settings

INVENTARIO_SERVICE_URL = settings.INVENTARIO_SERVICE_URL
HASH_SECRET = settings.HASH_KEY

@require_http_methods(["GET"])
def pedidos_view(request):
    """Display all pedidos"""
    pedidos = PedidoService.obtener_todos_pedidos()
    clientes = Cliente.objects.all()
    direcciones = Direccion.objects.all()
    productos = Producto.objects.all()

    context = {
        'pedidos': pedidos,
        'clientes': clientes,
        'direcciones': direcciones,
        'productos': productos
    }
    return render(request, "pedido_template.html", context)

def call_inventario_reservar(producto_id, cantidad, bodega_id=1):
    """
    Call manejador_inventarios service to reserve product with hash verification
    THIS CALLS THE OTHER SERVER
    """
    try:
        payload = {
            'producto_id': str(producto_id),
            'cantidad': str(cantidad),
            'bodega_id': str(bodega_id)
        }
        
        # Generate hash using ChecksService
        hash_value = ChecksService.generar_hash_hmac(payload)
        
        # Prepare FormData
        data = {
            'producto_id': payload['producto_id'],
            'cantidad': payload['cantidad'],
            'bodega_id': payload['bodega_id'],
            'hash': hash_value
        }
        
        # CALL OTHER SERVER HERE
        response = requests.post(
            f"{INVENTARIO_SERVICE_URL}/api/inventarios/reservar-producto/",
            data=data,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'success': False, 'error': f'Status {response.status_code}: {response.text}'}
    
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Connection error to inventory manager: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@require_http_methods(["POST"])
def pedido_create(request):
    """Create pedido and reserve inventory on other server"""
    try:
        cliente_id = request.POST.get('cliente_id')
        direccion_id = request.POST.get('direccion_id')
        precio_calculado = request.POST.get('precio_calculado')
        productos_str = request.POST.get('productos', '[]')
        bodega_id = request.POST.get('bodega_id', 1)
        
        productos = json.loads(productos_str)
        
        # Create pedido locally
        pedido = PedidoService.crear_pedido(cliente_id, direccion_id, precio_calculado)
        
        # For each product, call inventory manager to reserve
        for item in productos:
            producto_id = item['producto_id']
            cantidad = int(item['cantidad'])
            
            # CALL OTHER SERVER
            reserve_result = call_inventario_reservar(producto_id, cantidad, bodega_id)
            
            if not reserve_result.get('success'):
                # Rollback if reservation fails
                pedido.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Could not reserve product {producto_id}: {reserve_result.get("error")}'
                }, status=400)
            
            # Add product to pedido
            producto = Producto.objects.get(id=producto_id)
            ProductoPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=float(item.get('precio_unitario', 0)),
                subtotal=cantidad * float(item.get('precio_unitario', 0))
            )
        
        return JsonResponse({'success': True, 'pedido_id': pedido.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def pedido_detail(request):
    """Get pedido details"""
    pedido_id = request.GET.get('id')
    try:
        pedido = PedidoService.obtener_pedido(pedido_id)
        return JsonResponse({'id': pedido.id, 'precio_calculado': str(pedido.precio_calculado)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

@require_http_methods(["POST"])
def pedido_update(request):
    """Update pedido"""
    try:
        pedido_id = request.GET.get('id')
        precio_calculado = request.POST.get('precio_calculado')
        pedido = PedidoService.actualizar_pedido(pedido_id, precio_calculado=precio_calculado)
        return JsonResponse({'success': True, 'pedido_id': pedido.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["DELETE"])
def pedido_delete(request):
    """Delete pedido"""
    try:
        pedido_id = request.GET.get('id')
        PedidoService.eliminar_pedido(pedido_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)