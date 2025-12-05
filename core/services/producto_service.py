from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from core.models import Producto


# CREATE
def crear_producto(codigo_barras, tipo, peso, volumen, codigo):
    """
    Crea y retorna un nuevo Producto del catálogo.
    """
    return Producto.objects.create(
        codigo_barras=codigo_barras,
        tipo=tipo,
        peso=peso,
        volumen=volumen,
        codigo=codigo,
    )


# READ ALL
def obtener_todos_productos():
    """
    Retorna un queryset con todos los productos del catálogo.
    """
    return Producto.objects.all()


# READ BY ID
def obtener_producto_por_id(producto_id):
    """
    Retorna un producto por id o None si no existe.
    """
    try:
        return Producto.objects.get(id=producto_id)
    except ObjectDoesNotExist:
        return None


# UPDATE
def actualizar_producto(producto_id, **kwargs):
    """
    Actualiza solo los campos del Producto que vengan en kwargs.
    Retorna el producto actualizado o None si no existe.
    """
    producto = obtener_producto_por_id(producto_id)
    if not producto:
        return None

    for attr, value in kwargs.items():
        setattr(producto, attr, value)

    producto.save()
    return producto


# DELETE
def eliminar_producto(producto_id):
    """
    Elimina un producto por id.
    Retorna True si se eliminó, False si no existía.
    """
    producto = obtener_producto_por_id(producto_id)
    if producto:
        producto.delete()
        return True
    return False


# CONSULTAS AVANZADAS (opcionalmente útiles para el catálogo)

def obtener_productos_por_tipo(tipo):
    """
    Retorna todos los productos de un tipo dado.
    """
    return Producto.objects.filter(tipo=tipo)


def obtener_producto_por_codigo_barras(codigo_barras):
    """
    Retorna un producto por código de barras o None si no existe.
    """
    try:
        return Producto.objects.get(codigo_barras=codigo_barras)
    except ObjectDoesNotExist:
        return None


def obtener_promedio_peso_volumen_por_tipo(tipo):
    """
    Devuelve un dict con el promedio de peso y volumen para los productos de un tipo.
    Retorna None si no hay productos de ese tipo.
    """
    qs = Producto.objects.filter(tipo=tipo)
    if not qs.exists():
        return None

    agg = qs.aggregate(avg_peso=Avg('peso'), avg_volumen=Avg('volumen'))
    return {
        'tipo': tipo,
        'promedio_peso': float(agg['avg_peso']) if agg['avg_peso'] is not None else None,
        'promedio_volumen': float(agg['avg_volumen']) if agg['avg_volumen'] is not None else None,
    }
