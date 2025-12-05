# pedidos_service/core/services/inventario_client.py
import requests
from django.conf import settings
from core.services.checks_service import ChecksService

# pedidos_service/core/services/inventario_client.py
import requests
from django.conf import settings

INVENTARIO_SERVICE_URL = settings.INVENTARIO_SERVICE_URL


class InventarioClient:

    @staticmethod
    def consultar_disponibilidad(producto_id, bodega_id=1):
        try:
            resp = requests.get(
                f"{INVENTARIO_SERVICE_URL}/api/inventarios/disponibilidad/",
                params={
                    "producto_id": producto_id,
                    "bodega_id": bodega_id,
                },
                timeout=0.5,
            )
            if resp.status_code != 200:
                return {"disponible": False, "error": f"Status {resp.status_code}"}

            return resp.json()

        except requests.exceptions.RequestException as e:
            return {"disponible": False, "error": f"Error: {str(e)}"}

    @staticmethod
    def reservar_producto(producto_id, cantidad, bodega_id=1):
        try:
            data = {
                "producto_id": str(producto_id),
                "cantidad": str(cantidad),
                "bodega_id": str(bodega_id),
            }

            resp = requests.post(
                f"{INVENTARIO_SERVICE_URL}/api/inventarios/reservar-producto/",
                data=data,
                timeout=0.5,
            )

            if resp.status_code == 200:
                return resp.json()

            return {"success": False, "error": resp.text}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Error: {str(e)}"}