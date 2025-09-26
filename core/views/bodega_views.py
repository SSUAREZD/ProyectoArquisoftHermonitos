# core/views/bodega_views.py

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, Count, F, Avg, Q
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
    """Devuelve { id_bodega: {latitud, longitud, nombre, direccion, capacidad, total_disponible, total_reservado, ocupacion_pct} }.
    ocupacion_pct = ( (disponible + reservado) / capacidad ) * 100 si capacidad > 0.
    Si se pasa ?bodega_id= filtra solo esa bodega.
    (Se mantiene compatibilidad opcional: ya no se usa 'promedio', pero si se quisiera podría añadirse.)"""
    bodega_id = request.GET.get('bodega_id')
    qs = Bodega.objects.all()
    if bodega_id:
        qs = qs.filter(id=bodega_id)
    data = {}
    for b in qs:
        invs = Inventario.objects.filter(bodegas=b)
        agg = invs.aggregate(
            disp=Sum('cantidad_disponible'),
            res=Sum('cantidad_reservada'),
        )
        disp = agg['disp'] or 0
        res = agg['res'] or 0
        capacidad = float(b.capacidad) if b.capacidad else 0.0
        if capacidad > 0:
            ocupacion_pct = ((disp + res) / capacidad) * 100.0
        else:
            ocupacion_pct = 0.0
        data[b.id] = {
            'latitud': b.latitud,
            'longitud': b.longitud,
            'nombre': b.nombre,
            'direccion': b.direccion,
            'capacidad': capacidad,
            'total_disponible': disp,
            'total_reservado': res,
            'ocupacion_pct': round(ocupacion_pct, 2),
        }
    return JsonResponse(data)

# -----------------------------
# APIs NUEVAS PARA EL DASHBOARD
# -----------------------------

def kpis_api(request):
    """KPIs globales o filtrados por ?bodega_id="""
    bodega_id = request.GET.get('bodega_id')
    bodega = None
    if bodega_id:
        bodega = Bodega.objects.filter(id=bodega_id).first()

    if bodega:
        inv_qs = Inventario.objects.filter(bodegas=bodega)
        total_warehouses = 1
        sku_count = inv_qs.values('productos').distinct().count()
        stockout_skus = inv_qs.filter(cantidad_disponible=0).count()
        total_disponible = inv_qs.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_reservado = inv_qs.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
        total_capacity = bodega.capacidad or 1
    else:
        inv_qs = Inventario.objects.all()
        total_warehouses = Bodega.objects.count()
        sku_count = inv_qs.values('productos').distinct().count()
        stockout_skus = inv_qs.filter(cantidad_disponible=0).count()
        total_disponible = inv_qs.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        total_reservado = inv_qs.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
        total_capacity = Bodega.objects.aggregate(cap=Sum('capacidad'))['cap'] or 1

    occupancy = round(((total_disponible + total_reservado) / float(total_capacity)) * 100, 2)
    return JsonResponse({
        "total_warehouses": total_warehouses,
        "overall_occupancy_pct": occupancy,
        "sku_count": sku_count,
        "stockout_skus": stockout_skus,
        "filtered_bodega_id": bodega.id if bodega else None,
        "filtered_bodega_nombre": bodega.nombre if bodega else None,
    })

def mix_disponible_reservado_api(request):
    bodega_id = request.GET.get('bodega_id')
    labels, disponible, reservado = [], [], []
    if bodega_id:
        b = Bodega.objects.filter(id=bodega_id).first()
        if not b:
            return JsonResponse({"labels": [], "disponible": [], "reservado": []})
        invs = Inventario.objects.filter(bodegas=b)
        disp = invs.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
        res = invs.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
        labels.append(b.nombre)
        disponible.append(disp)
        reservado.append(res)
    else:
        for b in Bodega.objects.all():
            labels.append(b.nombre)
            invs = Inventario.objects.filter(bodegas=b)
            disp = invs.aggregate(total=Sum('cantidad_disponible'))['total'] or 0
            res = invs.aggregate(total=Sum('cantidad_reservada'))['total'] or 0
            disponible.append(disp)
            reservado.append(res)
    return JsonResponse({"labels": labels, "disponible": disponible, "reservado": reservado})

def aging_api(request):
    bodega_id = request.GET.get('bodega_id')
    hoy = now()
    buckets = {"0-30": 0, "31-60": 0, "61-90": 0, ">90": 0}
    invs = Inventario.objects.all()
    if bodega_id:
        invs = invs.filter(bodegas_id=bodega_id)
    for inv in invs:
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
    bodega_id = request.GET.get('bodega_id')
    qs_base = Inventario.objects.all()
    if bodega_id:
        qs_base = qs_base.filter(bodegas_id=bodega_id)
    qs = (qs_base
          .values(nombre=F('productos__codigo'))
          .annotate(total=Sum('cantidad_disponible'))
          .order_by('-total')[:5])
    labels = [x['nombre'] for x in qs]
    data = [x['total'] for x in qs]
    return JsonResponse({"labels": labels, "data": data})

def tareas_estado_api(request):
    bodega_id = request.GET.get('bodega_id')
    qs_tasks = TareaLogistica.objects.all()
    if bodega_id:
        # Filtra tareas ligadas a algún trabajador cuya bodegaAsignada coincida
        qs_tasks = qs_tasks.filter(
            Q(alistadores__bodegaAsignada_id=bodega_id) |
            Q(verificadores__bodegaAsignada_id=bodega_id) |
            Q(empacadores__bodegaAsignada_id=bodega_id) |
            Q(administradores__bodegaAsignada_id=bodega_id)
        )
    qs = (qs_tasks
          .values('estado')
          .annotate(total=Count('id', distinct=True))
          .order_by())
    labels = [x['estado'] for x in qs]
    data = [x['total'] for x in qs]
    return JsonResponse({"labels": labels, "data": data})
