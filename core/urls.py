from django.urls import path
from core.views.bodega_views import promedio_bodegas_view

urlpatterns = [
    path('bodegas/promedio/', promedio_bodegas_view, name='promedio_bodegas'),
]