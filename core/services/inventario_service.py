from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from core.models import Inventario, Producto, Bodega, Ubicacion
from django.utils.timezone import now

class InventarioService:
    """Service for managing Inventario CRUD operations"""
    
    @staticmethod
    def crear_inventario(producto_id, bodega_id, ubicacion_id=None, cantidad_disponible=0, cantidad_reservada=0):
        """Create a new inventory record"""
        try:
            producto = get_object_or_404(Producto, id=producto_id)
            bodega = get_object_or_404(Bodega, id=bodega_id)
            ubicacion = None
            if ubicacion_id:
                ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id)
            
            inventario = Inventario.objects.create(
                producto=producto,
                bodega=bodega,
                ubicacion=ubicacion,
                cantidad_disponible=cantidad_disponible,
                cantidad_reservada=cantidad_reservada,
                ultima_actualizacion=now()
            )
            return inventario
        except Exception as e:
            raise Exception(f"Error creating inventory: {str(e)}")
    
    @staticmethod
    def obtener_inventario(inventario_id):
        """Get an inventory record by ID"""
        return get_object_or_404(Inventario, id=inventario_id)
    
    @staticmethod
    def obtener_todos_inventarios():
        """Get all inventory records"""
        return Inventario.objects.all()
    
    @staticmethod
    def obtener_inventario_por_bodega(bodega_id):
        """Get all inventory for a specific bodega"""
        return Inventario.objects.filter(bodega_id=bodega_id).select_related('producto', 'bodega', 'ubicacion')
    
    @staticmethod
    def obtener_inventario_por_producto(producto_id):
        """Get all inventory locations for a specific product"""
        return Inventario.objects.filter(producto_id=producto_id).select_related('bodega', 'ubicacion')
    
    @staticmethod
    def obtener_disponibilidad_producto(producto_id):
        """Get total available quantity for a product across all bodegas"""
        total = Inventario.objects.filter(producto_id=producto_id).aggregate(
            total_disponible=Sum('cantidad_disponible')
        )['total_disponible'] or 0
        return total
    
    @staticmethod
    def obtener_disponibilidad_producto_bodega(producto_id, bodega_id):
        """Get available quantity for a product in a specific bodega"""
        inventario = Inventario.objects.filter(
            producto_id=producto_id,
            bodega_id=bodega_id
        ).first()
        return inventario.cantidad_disponible if inventario else 0
    
    @staticmethod
    def actualizar_inventario(inventario_id, **kwargs):
        """Update inventory with given fields"""
        inventario = get_object_or_404(Inventario, id=inventario_id)
        allowed_fields = ['cantidad_disponible', 'cantidad_reservada', 'ubicacion_id']
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(inventario, key, value)
        
        inventario.ultima_actualizacion = now()
        inventario.save()
        return inventario
    
    @staticmethod
    def reservar_producto(inventario_id, cantidad):
        """Reserve product quantity"""
        inventario = get_object_or_404(Inventario, id=inventario_id)
        
        if inventario.cantidad_disponible < cantidad:
            raise Exception(f"Insufficient stock. Available: {inventario.cantidad_disponible}, Requested: {cantidad}")
        
        inventario.cantidad_disponible -= cantidad
        inventario.cantidad_reservada += cantidad
        inventario.ultima_actualizacion = now()
        inventario.save()
        return inventario
    
    @staticmethod
    def liberar_reserva(inventario_id, cantidad):
        """Release reserved quantity back to available"""
        inventario = get_object_or_404(Inventario, id=inventario_id)
        
        if inventario.cantidad_reservada < cantidad:
            raise Exception(f"Cannot release more than reserved. Reserved: {inventario.cantidad_reservada}")
        
        inventario.cantidad_disponible += cantidad
        inventario.cantidad_reservada -= cantidad
        inventario.ultima_actualizacion = now()
        inventario.save()
        return inventario
    
    @staticmethod
    def confirmar_reserva(inventario_id, cantidad):
        """Confirm a reservation (consume reserved stock)"""
        inventario = get_object_or_404(Inventario, id=inventario_id)
        
        if inventario.cantidad_reservada < cantidad:
            raise Exception(f"Cannot confirm more than reserved. Reserved: {inventario.cantidad_reservada}")
        
        inventario.cantidad_reservada -= cantidad
        inventario.ultima_actualizacion = now()
        inventario.save()
        return inventario
    
    @staticmethod
    def eliminar_inventario(inventario_id):
        """Delete an inventory record"""
        inventario = get_object_or_404(Inventario, id=inventario_id)
        inventario.delete()
        return True
    
    @staticmethod
    def obtener_inventario_bajo(umbral=10):
        """Get inventory records below a certain threshold"""
        return Inventario.objects.filter(cantidad_disponible__lt=umbral).select_related('producto', 'bodega')
    
    @staticmethod
    def obtener_inventario_por_bodega_y_producto(bodega_id, producto_id):
        """Get inventory for a specific product in a specific bodega"""
        return Inventario.objects.filter(
            bodega_id=bodega_id,
            producto_id=producto_id
        ).select_related('producto', 'bodega', 'ubicacion').first()
    
    @staticmethod
    def contar_inventarios():
        """Count total inventory records"""
        return Inventario.objects.count()
    
    @staticmethod
    def contar_inventarios_por_bodega(bodega_id):
        """Count inventory records for a specific bodega"""
        return Inventario.objects.filter(bodega_id=bodega_id).count()
    
    @staticmethod
    def obtener_total_stock(bodega_id=None):
        """Get total stock (available + reserved) optionally filtered by bodega"""
        qs = Inventario.objects.all()
        if bodega_id:
            qs = qs.filter(bodega_id=bodega_id)
        
        agg = qs.aggregate(
            total_disponible=Sum('cantidad_disponible'),
            total_reservado=Sum('cantidad_reservada')
        )
        return {
            'disponible': agg['total_disponible'] or 0,
            'reservado': agg['total_reservado'] or 0,
            'total': (agg['total_disponible'] or 0) + (agg['total_reservado'] or 0)
        }
    
    @staticmethod
    def buscar_inventario(producto_codigo=None, bodega_nombre=None):
        """Search inventory by product code and/or bodega name"""
        qs = Inventario.objects.all()
        
        if producto_codigo:
            qs = qs.filter(producto__codigo__icontains=producto_codigo)
        
        if bodega_nombre:
            qs = qs.filter(bodega__nombre__icontains=bodega_nombre)
        
        return qs.select_related('producto', 'bodega', 'ubicacion')