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
        """Generate a simple SHA256 hex digest for a message (not recommended for transport integrity)."""
        canonical = ChecksService._canonicalize(mensaje)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generar_hash_hmac(mensaje):
        """Generate HMAC-SHA256 hex digest for a message using the configured secret key."""
        canonical = ChecksService._canonicalize(mensaje)
        key = (ChecksService.SECRET_KEY or "").encode('utf-8')
        return hmac.new(key, canonical.encode('utf-8'), hashlib.sha256).hexdigest()
    
    @staticmethod
    def verificar_integridad(hash_recibido, mensaje):
        """
        Verify if the received hash matches the message HMAC.
        Returns True when hash matches, False otherwise.
        """
        try:
            if not hash_recibido:
                return False
            expected = ChecksService.generar_hash_hmac(mensaje)
            # constant-time compare
            return hmac.compare_digest(str(hash_recibido), expected)
        except Exception:
            return False

    @staticmethod
    def _canonicalize(mensaje):
        """
        Produce a canonical string representation for the message:
         - If dict/list -> JSON with sorted keys and no extra spaces
         - If string that contains JSON -> parse then canonicalize
         - Otherwise -> plain string
        This must match the client's stable stringify (sorted keys, no spaces).
        """
        # If client sent a JSON string, try to parse it to normalize
        if isinstance(mensaje, str):
            try:
                parsed = json.loads(mensaje)
                mensaje = parsed
            except Exception:
                # leave as string
                return mensaje

        if isinstance(mensaje, (dict, list)):
            # separators=(',', ':') removes spaces -> deterministic compact form
            return json.dumps(mensaje, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        # fallback
        return str(mensaje)