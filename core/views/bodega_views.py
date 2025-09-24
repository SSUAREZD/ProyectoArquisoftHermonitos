from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.services.bodega_services import obtener_promedio_todas_bodegas

@api_view(['GET'])
def promedio_bodegas_view(request):
    data = obtener_promedio_todas_bodegas()
    return Response(data, status=status.HTTP_200_OK)