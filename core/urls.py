from django.urls import path
from core.views import bodega_views

urlpatterns = [
    path('bodegas/promedio/', bodega_views.promedio_bodegas_view),
]