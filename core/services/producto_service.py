from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from ..models import Producto


# CREATE
def crear_producto(codigo_barras, tipo, peso, volumen, codigo):
	"""Crea y retorna un nuevo Producto."""
	return Producto.objects.create(
		codigo_barras=codigo_barras,
		tipo=tipo,
		peso=peso,
		volumen=volumen,
		codigo=codigo,
	)


# READ ALL
def obtener_todos_productos():
	return Producto.objects.all()


# READ BY ID
def obtener_producto_por_id(producto_id):
	try:
		return Producto.objects.get(id=producto_id)
	except ObjectDoesNotExist:
		return None


# UPDATE
def actualizar_producto(producto_id, **kwargs):
	producto = obtener_producto_por_id(producto_id)
	if not producto:
		return None
	for attr, value in kwargs.items():
		setattr(producto, attr, value)
	producto.save()
	return producto


# DELETE
def eliminar_producto(producto_id):
	producto = obtener_producto_por_id(producto_id)
	if producto:
		producto.delete()
		return True
	return False


# Advanced Queries

def obtener_productos_por_tipo(tipo):
	return Producto.objects.filter(tipo=tipo)


def obtener_producto_por_codigo_barras(codigo_barras):
	try:
		return Producto.objects.get(codigo_barras=codigo_barras)
	except ObjectDoesNotExist:
		return None


def obtener_promedio_peso_volumen_por_tipo(tipo):
	"""Devuelve un dict con el promedio de peso y volumen para los productos de un tipo.

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

