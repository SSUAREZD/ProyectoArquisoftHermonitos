from django.http import JsonResponse
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

# --- Dashboard y API para bodegas ---
from django.db import models
from core.models import Bodega, Inventario

def dashboard_bodegas_view(request):
    return render(request, 'dashboard_bodegas.html')

def bodegas_data_api(request):
    bodegas = Bodega.objects.all()
    data = {}
    for bodega in bodegas:
        inventarios = Inventario.objects.filter(bodegas=bodega)
        promedio = inventarios.aggregate(promedio=models.Avg('cantidad_disponible'))['promedio'] or 0
        data[bodega.id] = {
            'latitud': bodega.latitud,
            'longitud': bodega.longitud,
            'nombre': bodega.nombre,
            'direccion': bodega.direccion,
            'promedio': promedio,
        }
    return JsonResponse(data)