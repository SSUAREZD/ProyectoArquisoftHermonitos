from django.db import models


# ============================================================
#                      USUARIO 
# ============================================================

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        abstract = True


class LiderLogistica(Usuario):
    pass


class Alistador(Usuario):
    lider_logistica = models.ForeignKey(LiderLogistica, null=True, on_delete=models.SET_NULL)
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='alistadores')


class Verificador(Usuario):
    lider_logistica = models.ForeignKey(LiderLogistica, null=True, on_delete=models.SET_NULL)
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='verificadores')


class Empacador(Usuario):
    lider_logistica = models.ForeignKey(LiderLogistica, null=True, on_delete=models.SET_NULL)
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='empacadores')


class Administrador(Usuario):
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='administradores')


class Vendedor(Usuario):
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='vendedores')


class Contador(Usuario):
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='contadores')


class Facturador(Usuario):
    bodega_asignada = models.ForeignKey('Bodega', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='facturadores')


# ============================================================
#                          DIRECCION
# ============================================================

class Direccion(models.Model):
    tipo = models.CharField(max_length=50)
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    dpto = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)
    referencias = models.TextField(blank=True, null=True)
    contacto_nombre = models.CharField(max_length=100)
    tel = models.CharField(max_length=20)


# ============================================================
#                          CLIENTE
# ============================================================

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    info_pago = models.CharField(max_length=255)


class CondicionPago(models.Model):
    nombre = models.CharField(max_length=100)
    info_pago = models.CharField(max_length=255)


class OrdenCompraCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordenes_compra')
    condicion_pago = models.ForeignKey(CondicionPago, on_delete=models.SET_NULL, null=True)


class CreditoCliente(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='credito')
    cupo_asignado = models.DecimalField(max_digits=12, decimal_places=2)
    cupo_disponible = models.DecimalField(max_digits=12, decimal_places=2)
    dias_plazo = models.IntegerField()


# ============================================================
#                          PRODUCTO
# ============================================================

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    peso = models.FloatField()
    volumen = models.FloatField()
    codigo = models.CharField(max_length=50)


# ============================================================
#                      PEDIDO + DETALLES
# ============================================================

class Pedido(models.Model):
    precio_calculado = models.DecimalField(max_digits=12, decimal_places=2)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    direccion = models.ForeignKey(Direccion, on_delete=models.SET_NULL, null=True)
    condicion_pago = models.ForeignKey(CondicionPago, null=True, on_delete=models.SET_NULL)
    orden_compra = models.ForeignKey(OrdenCompraCliente, null=True, blank=True, on_delete=models.SET_NULL)

    # clean many-to-many to easily get only the list of products
    productos = models.ManyToManyField(
        Producto,
        through='ProductoPedido',
        related_name='pedidos'
    )

class ProductoPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'      # ← THIS gives you pedido.items
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


# ============================================================
#                     ESTADO PEDIDO (HISTORIAL)
# ============================================================

class EstadoPedido(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)
    asignado = models.CharField(max_length=100)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historial')


# ============================================================
#                    GUIA DE ENVIO (1 - N)
# ============================================================

class Transportadora(models.Model):
    nombre = models.CharField(max_length=100)


class GuiaEnvio(models.Model):
    numero_guia = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)
    url = models.URLField()
    transportadora = models.ForeignKey(Transportadora, on_delete=models.SET_NULL, null=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='guias')


# ============================================================
#                     PAGO + MEDIO DE PAGO
# ============================================================

class MedioPago(models.Model):
    nombre = models.CharField(max_length=100)
    origen = models.CharField(max_length=100)


class Pago(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagos')
    medio_pago = models.ForeignKey(MedioPago, on_delete=models.SET_NULL, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField()
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)


# ============================================================
#              UBICACIONES, BODEGAS, INVENTARIO
# ============================================================

class Ubicacion(models.Model):
    codigo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=100)
    capacidad_max = models.FloatField()
    dimensiones = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)


class Bodega(models.Model):
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    direccion = models.CharField(max_length=255)
    capacidad = models.DecimalField(max_digits=10, decimal_places=2)
    ubicacion = models.OneToOneField(Ubicacion, on_delete=models.SET_NULL, null=True, related_name='bodega')


class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='inventarios')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True)
    cantidad_disponible = models.IntegerField()
    cantidad_reservada = models.IntegerField()
    ultima_actualizacion = models.DateTimeField()


# ============================================================
#                          EVIDENCIA
# ============================================================

class Evidencia(models.Model):
    tipo = models.CharField(max_length=100)
    url = models.URLField()
    foto = models.ImageField(upload_to='evidencias/')
    fecha_captura = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)

    capturado_por = models.CharField(max_length=100)
    alistador = models.ForeignKey(Alistador, null=True, on_delete=models.SET_NULL)
    empacador = models.ForeignKey(Empacador, null=True, on_delete=models.SET_NULL)
    verificador = models.ForeignKey(Verificador, null=True, on_delete=models.SET_NULL)


# ============================================================
#                     TAREA LOGÍSTICA
# ============================================================

class TareaLogistica(models.Model):
    tipo = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    prioridad = models.CharField(max_length=50)
    fecha_asignacion = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)

    pedido = models.ForeignKey(Pedido, null=True, on_delete=models.SET_NULL)
    alistador = models.ForeignKey(Alistador, null=True, blank=True, on_delete=models.SET_NULL)
    verificador = models.ForeignKey(Verificador, null=True, blank=True, on_delete=models.SET_NULL)
    empacador = models.ForeignKey(Empacador, null=True, blank=True, on_delete=models.SET_NULL)
    lider_logistica = models.ForeignKey(LiderLogistica, null=True, blank=True, on_delete=models.SET_NULL)
    administrador = models.ForeignKey(Administrador, null=True, blank=True, on_delete=models.SET_NULL)