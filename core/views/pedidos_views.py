from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from core.services.pedido_service import PedidoService
from core.models import Cliente, Direccion, Producto, Inventario, ProductoPedido


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


@require_http_methods(["GET"])
def check_inventory(request):
    """Check if a product is available in inventory"""
    producto_id = request.GET.get('producto_id')
    try:
        inventario = Inventario.objects.filter(producto_id=producto_id).first()
        if inventario and inventario.cantidad_disponible > 0:
            return JsonResponse({
                'disponible': True,
                'cantidad': inventario.cantidad_disponible
            })
        return JsonResponse({'disponible': False, 'cantidad': 0})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
def pedido_create(request):
    """Create a new pedido with products"""
    try:
        cliente_id = request.POST.get('cliente_id')
        direccion_id = request.POST.get('direccion_id')
        precio_calculado = request.POST.get('precio_calculado')
        productos_str = request.POST.get('productos', '[]')
        
        productos = json.loads(productos_str)
        
        pedido = PedidoService.crear_pedido(cliente_id, direccion_id, precio_calculado)
        
        # Add products to pedido
        for item in productos:
            producto = Producto.objects.get(id=item['producto_id'])
            ProductoPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=int(item['cantidad']),
                precio_unitario=0,  # You can calculate this based on your logic
                subtotal=0
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
        return JsonResponse({
            'id': pedido.id,
            'precio_calculado': str(pedido.precio_calculado),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@require_http_methods(["POST"])
def pedido_update(request):
    """Update a pedido"""
    try:
        pedido_id = request.GET.get('id')
        precio_calculado = request.POST.get('precio_calculado')

        update_data = {'precio_calculado': precio_calculado}
        
        pedido = PedidoService.actualizar_pedido(pedido_id, **update_data)
        return JsonResponse({'success': True, 'pedido_id': pedido.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["DELETE"])
def pedido_delete(request):
    """Delete a pedido"""
    try:
        pedido_id = request.GET.get('id')
        PedidoService.eliminar_pedido(pedido_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)