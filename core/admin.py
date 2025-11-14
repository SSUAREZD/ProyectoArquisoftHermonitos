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
    list_display = ("id", "bodega", "producto", "cantidad_disponible", "cantidad_reservada", "ultima_actualizacion")
    list_filter = ("bodega", "producto")
    search_fields = ("bodega__nombre", "producto__codigo")

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
    search_fields = ("numero_guia",)
    list_filter = ("transportadora", "estado")

class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

class EstadoPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

class ProductoPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "producto", "cantidad", "precio_unitario", "subtotal")
    list_filter = ("pedido",)
    search_fields = ("producto__codigo",)

class TransportadoraAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "tipo", "capacidad_max", "estado")
    search_fields = ("codigo", "tipo")
    list_filter = ("tipo", "estado")

class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "fecha_captura", "capturado_por")
    list_filter = ("tipo", "capturado_por")
    search_fields = ("tipo",)

class DireccionAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "ciudad", "pais", "contacto_nombre")
    search_fields = ("ciudad", "pais", "contacto_nombre")
    list_filter = ("tipo", "pais")

class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "precio_calculado", "cliente", "direccion")
    list_filter = ("cliente",)
    search_fields = ("cliente__nombre",)

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
safe_register(models.EstadoPedido, EstadoPedidoAdmin)
safe_register(models.ProductoPedido, ProductoPedidoAdmin)
safe_register(models.Transportadora, TransportadoraAdmin)
safe_register(models.Ubicacion, UbicacionAdmin)
safe_register(models.Evidencia, EvidenciaAdmin)
safe_register(models.Direccion, DireccionAdmin)
safe_register(models.Pedido, PedidoAdmin)
