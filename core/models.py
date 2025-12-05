from django.db import models

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
    producto_id = models.IntegerField()
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='inventarios')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True)
    cantidad_disponible = models.IntegerField()
    cantidad_reservada = models.IntegerField()
    ultima_actualizacion = models.DateTimeField()


# ============================================================
#                      USUARIOS LOGISTICOS
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

    
    pedido_id = models.IntegerField(null=True, blank=True)
    alistador = models.ForeignKey(Alistador, null=True, blank=True, on_delete=models.SET_NULL)
    verificador = models.ForeignKey(Verificador, null=True, blank=True, on_delete=models.SET_NULL)
    empacador = models.ForeignKey(Empacador, null=True, blank=True, on_delete=models.SET_NULL)
    lider_logistica = models.ForeignKey(LiderLogistica, null=True, blank=True, on_delete=models.SET_NULL)
    administrador = models.ForeignKey(Administrador, null=True, blank=True, on_delete=models.SET_NULL)
