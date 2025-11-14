from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import json
from core.services.inventario_service import InventarioService
from core.services.checks_service import ChecksService
from core.models import Bodega, Producto, Ubicacion, Inventario

@require_http_methods(["GET"])
def inventario_list(request):
    """Display all inventory"""
    inventarios = InventarioService.obtener_todos_inventarios()
    bodegas = Bodega.objects.all()
    productos = Producto.objects.all()
    ubicaciones = Ubicacion.objects.all()
    
    context = {
        'inventarios': inventarios,
        'bodegas': bodegas,
        'productos': productos,
        'ubicaciones': ubicaciones
    }
    return render(request, "inventario_template.html", context)

@require_http_methods(["POST"])
def inventario_create(request):
    """Create a new inventory record with integrity check"""
    try:
        # Get hash from request body
        hash_recibido = request.POST.get('hash')
        
        if not hash_recibido:
            return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)
        
        # Prepare data to verify
        data_to_verify = {
            'producto_id': request.POST.get('producto_id'),
            'bodega_id': request.POST.get('bodega_id'),
            'ubicacion_id': request.POST.get('ubicacion_id'),
            'cantidad_disponible': request.POST.get('cantidad_disponible', '0'),
            'cantidad_reservada': request.POST.get('cantidad_reservada', '0'),
        }
        
        print("HASH REC:", hash_recibido)
        print("EXPECTED:", ChecksService.generar_hash_hmac(data_to_verify))
        print("DATA:", data_to_verify)
        
        # Verify integrity
        if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
            return JsonResponse({'success': False, 'error': 'Hash verification failed - Data integrity compromised'}, status=400)
        
        # Proceed with creation
        producto_id = data_to_verify['producto_id']
        bodega_id = data_to_verify['bodega_id']
        ubicacion_id = data_to_verify['ubicacion_id']
        cantidad_disponible = int(data_to_verify['cantidad_disponible'])
        cantidad_reservada = int(data_to_verify['cantidad_reservada'])
        
        inventario = InventarioService.crear_inventario(
            producto_id, bodega_id, ubicacion_id, 
            cantidad_disponible, cantidad_reservada
        )
        return JsonResponse({'success': True, 'inventario_id': inventario.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def inventario_detail(request):
    """Get inventory details (no integrity check needed for read operations)"""
    inventario_id = request.GET.get('id')
    try:
        inventario = InventarioService.obtener_inventario(inventario_id)
        return JsonResponse({
            'id': inventario.id,
            'producto_id': inventario.producto_id,
            'bodega_id': inventario.bodega_id,
            'ubicacion_id': inventario.ubicacion_id,
            'cantidad_disponible': inventario.cantidad_disponible,
            'cantidad_reservada': inventario.cantidad_reservada,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

@require_http_methods(["POST"])
def inventario_update(request):
    """Update an inventory record with integrity check"""
    try:
        # Get hash from request body
        hash_recibido = request.POST.get('hash')
        inventario_id = request.GET.get('id')
        
        if not hash_recibido:
            return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)
        
        # Prepare data to verify
        data_to_verify = {
            'inventario_id': inventario_id,
            'cantidad_disponible': request.POST.get('cantidad_disponible', ''),
            'cantidad_reservada': request.POST.get('cantidad_reservada', ''),
            'ubicacion_id': request.POST.get('ubicacion_id', ''),
        }
        
        # Verify integrity
        if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
            return JsonResponse({'success': False, 'error': 'Hash verification failed - Data integrity compromised'}, status=400)
        
        # Proceed with update
        update_data = {}
        if data_to_verify['cantidad_disponible']:
            update_data['cantidad_disponible'] = int(data_to_verify['cantidad_disponible'])
        if data_to_verify['cantidad_reservada']:
            update_data['cantidad_reservada'] = int(data_to_verify['cantidad_reservada'])
        if data_to_verify['ubicacion_id']:
            update_data['ubicacion_id'] = data_to_verify['ubicacion_id']
        
        inventario = InventarioService.actualizar_inventario(inventario_id, **update_data)
        return JsonResponse({'success': True, 'inventario_id': inventario.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["DELETE"])
def inventario_delete(request):
    """Delete an inventory record with integrity check"""
    try:
        # Get hash from request body (for DELETE, hash goes in body)
        hash_recibido = request.POST.get('hash') or request.GET.get('hash')
        inventario_id = request.GET.get('id')
        
        if not hash_recibido:
            return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)
        
        # Prepare data to verify
        data_to_verify = {'inventario_id': inventario_id}
        
        # Verify integrity
        if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
            return JsonResponse({'success': False, 'error': 'Hash verification failed - Data integrity compromised'}, status=400)
        
        InventarioService.eliminar_inventario(inventario_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
def inventario_reservar(request):
    hash_recibido = request.POST.get('hash')

    if not hash_recibido:
        return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)

    # Canonical payload - all strings so it matches client hashing
    data_to_verify = {
        'producto_id': str(request.POST.get('producto_id')),
        'cantidad': str(request.POST.get('cantidad')),
        'bodega_id': str(request.POST.get('bodega_id')),
    }

    # Verificación de hash
    if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
        return JsonResponse({'success': False, 'error': 'Hash verification failed'}, status=403)

    # Buscar inventario correcto
    inventario = Inventario.objects.filter(
        productos_id=data_to_verify['producto_id'],
        bodegas_id=data_to_verify['bodega_id']
    ).first()

    if not inventario:
        return JsonResponse({'success': False, 'error': 'Inventory not found'}, status=404)

    cantidad = int(data_to_verify['cantidad'])
    if cantidad <= 0:
        return JsonResponse({'success': False, 'error': 'Quantity must be > 0'}, status=400)

    inventario = InventarioService.reservar_producto(inventario.id, cantidad)

    return JsonResponse({
        'success': True,
        'inventario_id': inventario.id,
        'disponible': inventario.cantidad_disponible,
        'reservado': inventario.cantidad_reservada
    })

@require_http_methods(["POST"])
def inventario_liberar_reserva(request):
    """Release reserved quantity with integrity check"""
    try:
        hash_recibido = request.POST.get('hash')
        
        if not hash_recibido:
            return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)
        
        data_to_verify = {
            'inventario_id': request.POST.get('inventario_id'),
            'cantidad': request.POST.get('cantidad'),
        }
        
        if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
            return JsonResponse({'success': False, 'error': 'Hash verification failed - Data integrity compromised'}, status=400)
        
        cantidad = int(data_to_verify['cantidad'])
        
        if cantidad <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'}, status=400)
        
        inventario = InventarioService.liberar_reserva(data_to_verify['inventario_id'], cantidad)
        return JsonResponse({
            'success': True,
            'inventario_id': inventario.id,
            'disponible': inventario.cantidad_disponible,
            'reservado': inventario.cantidad_reservada
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
def inventario_confirmar_reserva(request):
    """Confirm a reservation with integrity check"""
    try:
        hash_recibido = request.POST.get('hash')
        
        if not hash_recibido:
            return JsonResponse({'success': False, 'error': 'Missing hash parameter'}, status=400)
        
        data_to_verify = {
            'inventario_id': request.POST.get('inventario_id'),
            'cantidad': request.POST.get('cantidad'),
        }
        
        if not ChecksService.verificar_integridad(hash_recibido, data_to_verify):
            return JsonResponse({'success': False, 'error': 'Hash verification failed - Data integrity compromised'}, status=400)
        
        cantidad = int(data_to_verify['cantidad'])
        
        if cantidad <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be greater than 0'}, status=400)
        
        inventario = InventarioService.confirmar_reserva(data_to_verify['inventario_id'], cantidad)
        return JsonResponse({
            'success': True,
            'inventario_id': inventario.id,
            'reservado': inventario.cantidad_reservada
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# READ operations (no integrity check needed)
@require_http_methods(["GET"])
def inventario_bajo_stock(request):
    """Get inventory with low stock"""
    umbral = int(request.GET.get('umbral', 10))
    inventarios = InventarioService.obtener_inventario_bajo(umbral)
    data = [{
        'id': inv.id,
        'producto': inv.producto.codigo,
        'bodega': inv.bodega.nombre,
        'cantidad_disponible': inv.cantidad_disponible
    } for inv in inventarios]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def inventario_por_bodega(request):
    """Get all inventory for a bodega"""
    bodega_id = request.GET.get('bodega_id')
    inventarios = InventarioService.obtener_inventario_por_bodega(bodega_id)
    data = [{
        'id': inv.id,
        'producto': inv.producto.codigo,
        'disponible': inv.cantidad_disponible,
        'reservado': inv.cantidad_reservada
    } for inv in inventarios]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def inventario_por_producto(request):
    """Get all inventory locations for a product"""
    producto_id = request.GET.get('producto_id')
    inventarios = InventarioService.obtener_inventario_por_producto(producto_id)
    data = [{
        'id': inv.id,
        'bodega': inv.bodega.nombre,
        'disponible': inv.cantidad_disponible,
        'reservado': inv.cantidad_reservada,
        'ubicacion': inv.ubicacion.codigo if inv.ubicacion else 'N/A'
    } for inv in inventarios]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def inventario_disponibilidad_producto(request):
    """Get total available quantity for a product across all bodegas"""
    producto_id = request.GET.get('producto_id')
    total = InventarioService.obtener_disponibilidad_producto(producto_id)
    return JsonResponse({'producto_id': producto_id, 'total_disponible': total})

@require_http_methods(["GET"])
def inventario_disponibilidad_bodega_producto(request):
    """Get available quantity for a product in a specific bodega"""
    producto_id = request.GET.get('producto_id')
    bodega_id = request.GET.get('bodega_id')
    disponible = InventarioService.obtener_disponibilidad_producto_bodega(producto_id, bodega_id)
    return JsonResponse({
        'producto_id': producto_id,
        'bodega_id': bodega_id,
        'disponible': disponible
    })

@require_http_methods(["GET"])
def inventario_total_stock(request):
    """Get total stock (available + reserved) optionally filtered by bodega"""
    bodega_id = request.GET.get('bodega_id')
    stock = InventarioService.obtener_total_stock(bodega_id)
    return JsonResponse(stock)

@require_http_methods(["GET"])
def inventario_buscar(request):
    """Search inventory by product code and/or bodega name"""
    producto_codigo = request.GET.get('producto_codigo')
    bodega_nombre = request.GET.get('bodega_nombre')
    
    inventarios = InventarioService.buscar_inventario(producto_codigo, bodega_nombre)
    data = [{
        'id': inv.id,
        'producto': inv.producto.codigo,
        'bodega': inv.bodega.nombre,
        'disponible': inv.cantidad_disponible,
        'reservado': inv.cantidad_reservada
    } for inv in inventarios]
    return JsonResponse(data, safe=False)

@require_http_methods(["GET"])
def inventario_contar(request):
    """Count total inventory records"""
    total = InventarioService.contar_inventarios()
    return JsonResponse({'total_inventarios': total})

@require_http_methods(["GET"])
def inventario_contar_bodega(request):
    """Count inventory records for a specific bodega"""
    bodega_id = request.GET.get('bodega_id')
    total = InventarioService.contar_inventarios_por_bodega(bodega_id)
    return JsonResponse({'bodega_id': bodega_id, 'total_inventarios': total})