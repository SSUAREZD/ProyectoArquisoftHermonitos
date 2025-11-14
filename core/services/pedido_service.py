from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import Pedido, EstadoPedido

class PedidoService:
    """Service for managing Pedido CRUD operations"""
    
    @staticmethod
    def crear_pedido(cliente_id, direccion_id, precio_calculado, detalles=None):
        """Create a new pedido"""
        try:
            pedido = Pedido.objects.create(
                cliente_id=cliente_id,
                direccion_id=direccion_id,
                precio_calculado=precio_calculado
            )
            return pedido
        except Exception as e:
            raise Exception(f"Error creating pedido: {str(e)}")
    
    @staticmethod
    def obtener_pedido(pedido_id):
        """Get a pedido by ID"""
        return get_object_or_404(Pedido, id=pedido_id)
    
    @staticmethod
    def obtener_todos_pedidos():
        """Get all pedidos"""
        return Pedido.objects.all()
    
    @staticmethod
    def obtener_pedidos_por_cliente(cliente_id):
        """Get all pedidos for a specific cliente"""
        return Pedido.objects.filter(cliente_id=cliente_id)
    
    @staticmethod
    def obtener_pedidos_por_estado(estado_id):
        """Get all pedidos with a specific estado"""
        return Pedido.objects.filter(estadosPedido_id=estado_id)
    
    @staticmethod
    def actualizar_pedido(pedido_id, **kwargs):
        """Update a pedido with given fields"""
        pedido = get_object_or_404(Pedido, id=pedido_id)
        allowed_fields = ['precio_calculado', 'guiasEnvio_id', 'cliente_id', 'estadosPedido_id', 'direccion_id']
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(pedido, key, value)
        
        pedido.save()
        return pedido
    
    @staticmethod
    def eliminar_pedido(pedido_id):
        """Delete a pedido"""
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.delete()
        return True
    
    @staticmethod
    def obtener_pedidos_por_rango_precio(precio_min, precio_max):
        """Get pedidos within a price range"""
        return Pedido.objects.filter(precio_calculado__gte=precio_min, precio_calculado__lte=precio_max)
    
    @staticmethod
    def contar_pedidos():
        """Count total pedidos"""
        return Pedido.objects.count()