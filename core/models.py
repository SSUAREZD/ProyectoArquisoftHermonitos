from django.db import models

# ----------- Trabajadores Abstractos y Subclases -----------
class Trabajador(models.Model):
    nombre = models.CharField(max_length=100)
    class Meta:
        abstract = True

class LiderLogistica(Trabajador):
    pass

class Alistador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    bodegaAsignada = models.ForeignKey('Bodega', related_name='alistadores', blank=True, null=True, on_delete=models.SET_NULL)

class Verificador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    bodegaAsignada = models.ForeignKey('Bodega', related_name='verificadores', blank=True, null=True, on_delete=models.SET_NULL)

class Empacador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    bodegaAsignada = models.ForeignKey('Bodega', related_name='empacadores', blank=True, null=True, on_delete=models.SET_NULL)

class Administrador(Trabajador):
    bodegaAsignada = models.ForeignKey('Bodega', related_name='administradores', blank=True, null=True, on_delete=models.SET_NULL)

class Vendedor(Trabajador):
    bodegaAsignada = models.ForeignKey('Bodega', related_name='vendedores', blank=True, null=True, on_delete=models.SET_NULL)

class Contador(Trabajador):
    bodegaAsignada = models.ForeignKey('Bodega', related_name='contadores', blank=True, null=True, on_delete=models.SET_NULL)

class Facturador(Trabajador):
    bodegaAsignada = models.ForeignKey('Bodega', related_name='facturadores', blank=True, null=True, on_delete=models.SET_NULL)

# ----------- Entidades de negocio -----------
class Pedido(models.Model):
    precio_calculado = models.DecimalField(max_digits=10, decimal_places=2)
    guiasEnvio = models.ForeignKey('GuiaEnvio', on_delete=models.SET_NULL, null=True)
    direccion = models.OneToOneField('Direccion', on_delete=models.SET_NULL, null=True, related_name='pedido_asociado')
    clientes = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True)
    estadosPedido = models.ForeignKey('EstadoPedido', on_delete=models.SET_NULL, null=True)

class Bodega(models.Model):
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    capacidad = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.OneToOneField('Ubicacion', on_delete=models.SET_NULL, null=True, related_name='bodega_asociada')

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    peso = models.FloatField()
    volumen = models.FloatField()
    codigo = models.CharField(max_length=50)

class GuiaEnvio(models.Model):
    numero_guia = models.IntegerField()
    direccion = models.CharField(max_length=255)
    transportadora = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    url = models.URLField()
    transportadoras = models.ForeignKey('Transportadora', on_delete=models.SET_NULL, null=True)

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    info_pago = models.CharField(max_length=255)

class Factura(models.Model):
    metodo_pago = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    pedidos = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True)

class EstadoPedido(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField()
    asignado = models.CharField(max_length=100)
    observacion = models.TextField(blank=True, null=True)
    evidencias = models.ForeignKey('Evidencia',on_delete=models.SET_NULL, null=True)

class DetallePedido(models.Model):
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    pedidos = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True)
    productos = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)

class Transportadora(models.Model):
    nombre = models.CharField(max_length=100)

class Inventario(models.Model):
    cantidad_disponible = models.IntegerField()
    cantidad_reservada = models.IntegerField()
    ultima_actualizacion = models.DateTimeField()
    productos = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)
    bodegas = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='inventarios')
    ubicaciones = models.ForeignKey('Ubicacion', on_delete=models.SET_NULL, null=True)

class Ubicacion(models.Model):
    codigo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=100)
    capacidad_max = models.FloatField()
    dimensiones = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)
    bodega = models.OneToOneField('Bodega', on_delete=models.CASCADE, related_name='ubicacion_actual')

class Evidencia(models.Model):
    tipo = models.CharField(max_length=100)
    url = models.URLField()
    foto = models.ImageField(upload_to='evidencias/')
    fecha_captura = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)
    capturado_por = models.CharField(max_length=100)
    alistadores = models.ForeignKey('Alistador', on_delete=models.SET_NULL, null=True)
    empacadores = models.ForeignKey('Empacador', on_delete=models.SET_NULL, null=True)
    verificadores = models.ForeignKey('Verificador', on_delete=models.SET_NULL, null=True)

class Direccion(models.Model):
    tipo = models.CharField(max_length=50)
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    dpto = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    referencias = models.TextField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, null=True, related_name='direccion_entrega')

class TareaLogistica(models.Model):
    tipo = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    prioridad = models.CharField(max_length=50)
    fecha_asignacion = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    pedidos = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True)
    alistadores = models.ForeignKey('Alistador', on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_alistador')
    verificadores = models.ForeignKey('Verificador', on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_verificador')
    empacadores = models.ForeignKey('Empacador', on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_empacador')
    lider_logistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_lider')
    administradores = models.ForeignKey('Administrador', on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_admin')