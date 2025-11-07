import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.services.producto_service import (
    crear_producto,
    obtener_todos_productos,
    obtener_producto_por_id,
    actualizar_producto,
    eliminar_producto,
    obtener_productos_por_tipo,
    obtener_producto_por_codigo_barras,
)


def _serialize_producto(p):
    return {
        'id': p.id,
        'codigo_barras': p.codigo_barras,
        'tipo': p.tipo,
        'peso': float(p.peso) if p.peso is not None else None,
        'volumen': float(p.volumen) if p.volumen is not None else None,
        'codigo': p.codigo,
    }


@csrf_exempt
def productos_list_create_api(request):
    """GET: lista de productos (puede filtrar por ?tipo= o ?codigo_barras=)
    POST: crea un producto (JSON body con codigo_barras, tipo, peso, volumen, codigo)
    """
    if request.method == 'GET':
        codigo_barras = request.GET.get('codigo_barras')
        tipo = request.GET.get('tipo')
        if codigo_barras:
            p = obtener_producto_por_codigo_barras(codigo_barras)
            if not p:
                return JsonResponse({'error': 'Producto no encontrado'}, status=404)
            return JsonResponse(_serialize_producto(p))

        if tipo:
            qs = obtener_productos_por_tipo(tipo)
        else:
            qs = obtener_todos_productos()

        data = [_serialize_producto(p) for p in qs]
        return JsonResponse(data, safe=False)

    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        required = ['codigo_barras', 'tipo', 'peso', 'volumen', 'codigo']
        if not all(k in body for k in required):
            return JsonResponse({'error': f'Campos requeridos: {required}'}, status=400)
        p = crear_producto(
            codigo_barras=body['codigo_barras'],
            tipo=body['tipo'],
            peso=body['peso'],
            volumen=body['volumen'],
            codigo=body['codigo'],
        )
        return JsonResponse(_serialize_producto(p), status=201)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def producto_detail_api(request, producto_id):
    """GET, PUT, DELETE sobre un producto por id."""
    p = obtener_producto_por_id(producto_id)
    if not p:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    if request.method == 'GET':
        return JsonResponse(_serialize_producto(p))

    if request.method == 'PUT':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        # Solo actualiza los campos que vienen en el body
        allowed = ['codigo_barras', 'tipo', 'peso', 'volumen', 'codigo']
        updates = {k: body[k] for k in allowed if k in body}
        prod = actualizar_producto(producto_id, **updates)
        if not prod:
            return JsonResponse({'error': 'No se pudo actualizar'}, status=400)
        return JsonResponse(_serialize_producto(prod))

    if request.method == 'DELETE':
        ok = eliminar_producto(producto_id)
        if ok:
            return JsonResponse({'deleted': True})
        return JsonResponse({'deleted': False}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
