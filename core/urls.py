from django.urls import path
from core.views.bodega_views import mapa_bodegas_view

urlpatterns = [
    path('bodegas/mapa/', mapa_bodegas_view, name='mapa_bodegas'),
]