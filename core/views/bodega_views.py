# core/views/bodega_views.py

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, Count, F, Avg
from django.utils.timezone import now

from core.models import Bodega, Inventario, TareaLogistica

# -----------------------------
# VISTAS HTML
# -----------------------------

def mapa_bodegas_view(request):
    """
    Renderiza la página del mapa. El HTML usa fetch('/api/bodegas/') para cargar datos.
    """
    return render(request, "mapa_bodegas.html")

def dashboard_bodegas_view(request):
    """
    Renderiza la página del dashboard. El HTML usa endpoints /api/... para gráficos.
    """
    return render(request, "dashboard_bodegas.html")

# -----------------------------
# API: Datos de bodegas para el mapa (la que usa tu HTML actual)
# -----------------------------

def bodegas_data_api(request):
    """
    Devuelve { id_bodega: {latitud, longitud, nombre, direccion, promedio} }
    El 'promedio' aquí es el promedio de cantidad_disponible como proxy rápido.
    Si prefieres otra fórmula, ajusta abajo.
    """
    data = {}
    for bodega in Bodega.objects.all():
        invs = Inventario.objects.filter(bodegas=bodega)
        promedio = invs.aggregate(prom=Avg('cantidad_disponible'))['prom'] or 0
        data[bodega.id] = {
            'latitud': bodega.latitud,
            'longitud': bodega.longitud,
            'nombre': bodega.nombre,
            'direccion': bodega.direccion,
            'promedio': float(promedio),  # asegurar JSON serializable
        }
    return JsonResponse(data)

# -----------------------------
# APIs NUEVAS PARA EL DASHBOARD
# -----------------------------

def kpis_api(request):
    total_warehouses = Bodega.objects.count()
    sku_count = Inventario.objects.values('productos').distinct().count()
    stockout_skus = Inventario.objects.filter(cantidad_disponible=0).count()

    total_disponible = Inventario.objects.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
    total_reservado = Inventario.objects.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
    total_capacity = Bodega.objects.aggregate(cap=Sum('capacidad'))['cap'] or 1  # evita división por cero
    occupancy = round(((total_disponible + total_reservado) / float(total_capacity)) * 100, 2)

    return JsonResponse({
        "total_warehouses": total_warehouses,
        "overall_occupancy_pct": occupancy,
        "sku_count": sku_count,
        "stockout_skus": stockout_skus
    })

def mix_disponible_reservado_api(request):
    labels, disponible, reservado = [], [], []
    for b in Bodega.objects.all():
        labels.append(b.nombre)
        invs = Inventario.objects.filter(bodegas=b)
        disp = invs.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        res = invs.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
        disponible.append(disp)
        reservado.append(res)
    return JsonResponse({"labels": labels, "disponible": disponible, "reservado": reservado})

def aging_api(request):
    hoy = now()
    buckets = {"0-30": 0, "31-60": 0, "61-90": 0, ">90": 0}
    for inv in Inventario.objects.all():
        if not inv.ultima_actualizacion:
            continue
        dias = (hoy - inv.ultima_actualizacion).days
        qty = inv.cantidad_disponible or 0
        if dias <= 30: buckets["0-30"] += qty
        elif dias <= 60: buckets["31-60"] += qty
        elif dias <= 90: buckets["61-90"] += qty
        else: buckets[">90"] += qty
    return JsonResponse({"labels": list(buckets.keys()), "data": list(buckets.values())})

def top_skus_api(request):
    qs = (Inventario.objects
          .values(nombre=F('productos__codigo'))
          .annotate(total=Sum('cantidad_disponible'))
          .order_by('-total')[:5])
    labels = [x['nombre'] for x in qs]
    data = [x['total'] for x in qs]
    return JsonResponse({"labels": labels, "data": data})

def tareas_estado_api(request):
    qs = (TareaLogistica.objects
          .values('estado')
          .annotate(total=Count('id'))
          .order_by())
    labels = [x['estado'] for x in qs]
    data = [x['total'] for x in qs]
    return JsonResponse({"labels": labels, "data": data})
