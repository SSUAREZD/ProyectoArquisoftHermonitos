import json
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.services.bodega_services import obtener_promedio_todas_bodegas

def mapa_bodegas_view(request):
    bodegas = obtener_promedio_todas_bodegas()
    
    bodegas_json = {}
    for k, v in bodegas.items():
        bodegas_json[k] = {
            'promedio': v['promedio'],
            'nombre': v['nombre'],
            'direccion': v['direccion'],
            'latitud': v['latitud'],
            'longitud': v['longitud'],
        }

    return render(request, "mapa_bodegas.html", {
        "bodegas_json": json.dumps(bodegas_json)
    })