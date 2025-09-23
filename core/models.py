from django.db import models

class Trabajador(models.Model):
    nombre = models.CharField(max_length=100)
    class Meta:
        abstract = True

class LiderLogistica(Trabajador):
    pass

class Alistador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Verificador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Empacador(Trabajador):
    liderLogistica = models.ForeignKey('LiderLogistica', on_delete=models.SET_NULL, null=True)
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Administrador(Trabajador):
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Vendedor(models.Model):
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Contador(models.Model):
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Facturador(models.Model):
    #relaciones
    bodegaAsignada = models.ForeignKey('Bodega', related_name='trabajadores', blank=True, null=True, on_delete=models.SET_NULL)

class Pedido(models.Model):
    precio_calculado = models.DecimalField(max_digits=10, decimal_places=2)
    #relaciones
    guiasEnvio = models.ForeignKey('GuiaEnvio', on_delete=models.SET_NULL, null=True)
    direcciones = models.OneToOneField('Direccion', on_delete=models.SET_NULL, null=True)
    clientes = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True)
    estadosPedido = models.ForeignKey('EstadoPedido', on_delete=models.SET_NULL, null=True)

class Bodega(models.Model):
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    capacidad = models.DecimalField(max_digits=10, decimal_places=2)
    #relaciones
    ubicacion = models.OneToOneField('Ubicacion', on_delete=models.SET_NULL, null=True)
    


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
    #relaciones
    transportadoras = models.ForeignKey('Transportadora', on_delete=models.SET_NULL, null=True)


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    info_pago = models.CharField(max_length=255)


class Factura(models.Model):
    metodo_pago = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    #relaciones
    pedidos = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True)


class EstadoPedido(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField()
    asignado = models.CharField(max_length=100)
    observacion = models.TextField(blank=True, null=True)
    #relaciones
    evidencias = models.ForeignKey('Evidencia', blank=True)


class DetallePedido(models.Model):
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    #relaciones
    pedidos = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True)
    productos = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)


class Transportadora(models.Model):
    nombre = models.CharField(max_length=100)


class Inventario(models.Model):
    cantidad_disponible = models.IntegerField()
    cantidad_reservada = models.IntegerField()
    ultima_actualizacion = models.DateTimeField()
    #relaciones
    productos = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)
    bodegas = models.ForeignKey('Bodega', on_delete=models.CASCADE)
    ubicaciones = models.ForeignKey('Ubicacion', on_delete=models.SET_NULL, null=True)
    

class Ubicacion(models.Model):
    codigo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=100)
    capacidad_max = models.FloatField()
    dimensiones = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)
    #relaciones
    bodegas = models.OneToOneField('Bodega', on_delete=models.CASCADE)


class Evidencia(models.Model):
    tipo = models.CharField(max_length=100)
    url = models.URLField()
    foto = models.ImageField(upload_to='evidencias/')
    fecha_captura = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)
    capturado_por = models.CharField(max_length=100)
    #relaciones
    trabajadores = models.ForeignKey('Trabajador', on_delete=models.SET_NULL, null=True)


class Direccion(models.Model):
    tipo = models.CharField(max_length=50)
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    dpto = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    referencias = models.TextField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)
    #relaciones
    pedido = models.OneToOneField('Pedido', on_delete=models.CASCADE, related_name='direccion_pedido', null=True)


class TareaLogistica(models.Model):
    tipo = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    prioridad = models.CharField(max_length=50)
    fecha_asignacion = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    #relaciones
    pedidos = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True)
    trabajadores = models.ForeignKey('Trabajador', on_delete=models.SET_NULL, null=True)