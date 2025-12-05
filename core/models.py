from django.db import models


# ============================================================
#                     CLIENTE / DIRECCION
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

    productos = models.ManyToManyField(
        Producto,
        through='ProductoPedido',
        related_name='pedidos'
    )


class ProductoPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)


class EstadoPedido(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)
    asignado = models.CharField(max_length=100)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historial')


# ============================================================
#                    GUIA DE ENVIO / TRANSPORTADORA
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
