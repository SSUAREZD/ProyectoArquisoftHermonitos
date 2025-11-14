import hashlib
import hmac
import json
from django.conf import settings


class ChecksService:
    """Service for verifying message integrity using hash"""
    
    # Secret key for HMAC - store this in environment variables in production!
    SECRET_KEY = settings.HASH_KEY
    
    @staticmethod
    def generar_hash(mensaje):
        """Generate a hash for a message"""
        if isinstance(mensaje, dict):
            mensaje = json.dumps(mensaje, sort_keys=True)
        elif not isinstance(mensaje, str):
            mensaje = str(mensaje)
        
        return hashlib.sha256(mensaje.encode()).hexdigest()
    
    @staticmethod
    def generar_hash_hmac(mensaje):
        """Generate HMAC hash for a message (more secure)"""
        if isinstance(mensaje, dict):
            mensaje = json.dumps(mensaje, sort_keys=True)
        elif not isinstance(mensaje, str):
            mensaje = str(mensaje)
        
        return hmac.new(
            ChecksService.SECRET_KEY.encode(),
            mensaje.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verificar_integridad(hash_recibido, mensaje):
        """
        Verify if the received hash matches the message hash
        
        Args:
            hash_recibido: Hash received from client
            mensaje: The message/data to verify
        
        Returns:
            bool: True if hash is valid, False otherwise
        """
        try:
            # Generate hash for the message
            hash_calculado = ChecksService.generar_hash_hmac(mensaje)
            
            # Compare using constant-time comparison to prevent timing attacks
            return hmac.compare_digest(hash_recibido, hash_calculado)
        except Exception as e:
            print(f"Error verifying hash: {str(e)}")
            return False
    
