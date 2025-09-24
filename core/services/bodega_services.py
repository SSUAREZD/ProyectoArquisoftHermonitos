from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from ..models import Bodega

# CREATE
def crear_bodega(codigo, nombre, ciudad, direccion, capacidad):
    return Bodega.objects.create(
        codigo=codigo,
        nombre=nombre,
        ciudad=ciudad,
        direccion=direccion,
        capacidad=capacidad
    )

# READ ALL
def obtener_todas_bodegas():
    return Bodega.objects.all()

# READ BY ID
def obtener_bodega_por_id(bodega_id):
    try:
        return Bodega.objects.get(id=bodega_id)
    except ObjectDoesNotExist:
        return None

# UPDATE
def actualizar_bodega(bodega_id, **kwargs):
    bodega = obtener_bodega_por_id(bodega_id)
    if not bodega:
        return None
    for attr, value in kwargs.items():
        setattr(bodega, attr, value)
    bodega.save()
    return bodega

# DELETE
def eliminar_bodega(bodega_id):
    bodega = obtener_bodega_por_id(bodega_id)
    if bodega:
        bodega.delete()
        return True
    return False

# Advanced Queries

def obtener_bodegas_por_ciudad(ciudad):
    return Bodega.objects.filter(ciudad=ciudad)

def obtener_promedio_inventario(bodega_id):
    bodega = obtener_bodega_por_id(bodega_id)
    if not bodega:
        return None
    inventarios = bodega.inventarios.all()
    total = 0
    count = 0

    for inv in inventarios:
        if inv.cantidad_reservada and inv.cantidad_reservada != 0:
            total += inv.cantidad_disponible / (inv.cantidad_reservada+ inv.cantidad_disponible)
            count += 1

    if count == 0:
        return None 

    return (total / count)

def obtener_promedio_todas_bodegas():
    bodegas = Bodega.objects.all()
    res={}

    for bodega in bodegas:
        promedio = obtener_promedio_inventario(bodega.id)
        if promedio is not None:
            res[bodega.id] = {
    "promedio": promedio,
    "nombre": bodega.nombre,
    "direccion": bodega.direccion,
    "latitud": float(bodega.latitud),
    "longitud": float(bodega.longitud),
}
            
    return res