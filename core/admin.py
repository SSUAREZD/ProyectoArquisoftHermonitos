from django.contrib import admin
from . import models

# Utilidad para intentar registrar sin duplicar
def safe_register(model, admin_class=None):
	try:
		if admin_class:
			admin.site.register(model, admin_class)
		else:
			admin.site.register(model)
	except admin.sites.AlreadyRegistered:
		pass

class BodegaAdmin(admin.ModelAdmin):
	list_display = ("id", "codigo", "nombre", "ciudad", "capacidad")
	search_fields = ("codigo", "nombre", "ciudad")
	list_filter = ("ciudad",)

class InventarioAdmin(admin.ModelAdmin):
	list_display = ("id", "bodegas", "productos", "cantidad_disponible", "cantidad_reservada", "ultima_actualizacion")
	list_filter = ("bodegas", "productos")
	search_fields = ("bodegas__nombre", "productos__codigo")

class ProductoAdmin(admin.ModelAdmin):
	list_display = ("id", "codigo", "codigo_barras", "tipo", "peso", "volumen")
	search_fields = ("codigo", "codigo_barras", "tipo")

class TareaLogisticaAdmin(admin.ModelAdmin):
	list_display = ("id", "tipo", "estado", "prioridad", "fecha_asignacion", "fecha_fin")
	list_filter = ("estado", "prioridad")
	search_fields = ("tipo", "estado")

class TrabajadorBaseAdmin(admin.ModelAdmin):
	list_display = ("id", "nombre")
	search_fields = ("nombre",)

class GuiaEnvioAdmin(admin.ModelAdmin):
	list_display = ("id", "numero_guia", "transportadora", "estado")
	search_fields = ("numero_guia", "transportadora", "estado")

class ClienteAdmin(admin.ModelAdmin):
	list_display = ("id", "nombre")
	search_fields = ("nombre",)

class FacturaAdmin(admin.ModelAdmin):
	list_display = ("id", "metodo_pago", "fecha")
	list_filter = ("metodo_pago",)

class EstadoPedidoAdmin(admin.ModelAdmin):
	list_display = ("id", "nombre", "fecha_hora", "asignado")
	list_filter = ("nombre",)

class DetallePedidoAdmin(admin.ModelAdmin):
	list_display = ("id", "pedidos", "productos", "cantidad", "precio_unitario", "subtotal")
	list_filter = ("productos",)

class TransportadoraAdmin(admin.ModelAdmin):
	list_display = ("id", "nombre")

class UbicacionAdmin(admin.ModelAdmin):
	list_display = ("id", "codigo", "tipo", "capacidad_max", "estado")
	search_fields = ("codigo", "tipo")

class EvidenciaAdmin(admin.ModelAdmin):
	list_display = ("id", "tipo", "fecha_captura", "capturado_por")
	list_filter = ("tipo", "capturado_por")

class DireccionAdmin(admin.ModelAdmin):
	list_display = ("id", "tipo", "ciudad", "pais", "contacto_nombre")
	search_fields = ("ciudad", "pais", "contacto_nombre")

class PedidoAdmin(admin.ModelAdmin):
	list_display = ("id", "precio_calculado", "clientes", "estadosPedido")

# Registro de modelos
safe_register(models.Bodega, BodegaAdmin)
safe_register(models.Inventario, InventarioAdmin)
safe_register(models.Producto, ProductoAdmin)
safe_register(models.TareaLogistica, TareaLogisticaAdmin)
safe_register(models.LiderLogistica, TrabajadorBaseAdmin)
safe_register(models.Alistador, TrabajadorBaseAdmin)
safe_register(models.Verificador, TrabajadorBaseAdmin)
safe_register(models.Empacador, TrabajadorBaseAdmin)
safe_register(models.Administrador, TrabajadorBaseAdmin)
safe_register(models.Vendedor, TrabajadorBaseAdmin)
safe_register(models.Contador, TrabajadorBaseAdmin)
safe_register(models.Facturador, TrabajadorBaseAdmin)
safe_register(models.GuiaEnvio, GuiaEnvioAdmin)
safe_register(models.Cliente, ClienteAdmin)
safe_register(models.Factura, FacturaAdmin)
safe_register(models.EstadoPedido, EstadoPedidoAdmin)
safe_register(models.DetallePedido, DetallePedidoAdmin)
safe_register(models.Transportadora, TransportadoraAdmin)
safe_register(models.Ubicacion, UbicacionAdmin)
safe_register(models.Evidencia, EvidenciaAdmin)
safe_register(models.Direccion, DireccionAdmin)
safe_register(models.Pedido, PedidoAdmin)
