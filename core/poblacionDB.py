import os
import django
import random
from datetime import datetime, timedelta

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoArquisoft.settings')
django.setup()

# Importar modelos
from core.models import Cliente, Producto, Bodega, Inventario

# Datos realistas colombianos
NOMBRES_BODEGA = [
    "Bodega Norte Bogotá",
    "Bodega Sur Bogotá",
    "Bodega Medellín",
    "Bodega Cali",
    "Bodega Barranquilla"
]
CIUDADES = [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"
]
DIRECCIONES = [
    "Cra 15 # 100-25, Bogotá",
    "Av. El Poblado # 45-67, Medellín",
    "Calle 13 # 23-45, Cali",
    "Cra 46 # 80-120, Barranquilla",
    "Av. Pedro de Heredia # 12-34, Cartagena"
]
PRODUCTOS = [
    ("Uniforme Ejecutivo", "Ropa"),
    ("Botas de Seguridad", "Calzado"),
    ("Casco Industrial", "Protección"),
    ("Guantes Anticorte", "Protección"),
    ("Chaqueta Reflectiva", "Ropa"),
    ("Camisa Polo", "Ropa"),
    ("Pantalón Cargo", "Ropa"),
    ("Zapatos Dieléctricos", "Calzado"),
    ("Gafas de Seguridad", "Protección"),
    ("Tapabocas N95", "Protección")
]

def create_productos():
    for nombre, tipo in PRODUCTOS:
        Producto.objects.create(
            codigo_barras=str(random.randint(7700000000000, 7700999999999)),
            tipo=tipo,
            peso=round(random.uniform(0.2, 2.0), 2),
            volumen=round(random.uniform(0.05, 0.5), 2),
            codigo=f"DOT-{random.randint(1000,9999)}",
            nombre=nombre
        )

def create_bodegas():
    for i in range(len(NOMBRES_BODEGA)):
        Bodega.objects.create(
            codigo=f"BOD{i+1:03}",
            nombre=NOMBRES_BODEGA[i],
            ciudad=CIUDADES[i],
            direccion=DIRECCIONES[i],
            capacidad=round(random.uniform(500.0, 2000.0), 2),
            latitud=[4.75, 4.65, 6.25, 3.45, 10.4][i],      # Coordenadas aproximadas
            longitud=[-74.03, -74.1, -75.57, -76.53, -75.5][i]
        )

def create_inventario():
    bodegas = list(Bodega.objects.all())
    productos = list(Producto.objects.all())

    for bodega in bodegas:
        productos_sample = random.sample(productos, k=min(5, len(productos)))
        inventario_tipo = random.choice(["bajo", "medio", "alto", "muy_alto"])

        for producto in productos_sample:
            if inventario_tipo == "bajo":
                cantidad_disponible = random.randint(5, 20)
            elif inventario_tipo == "medio":
                cantidad_disponible = random.randint(21, 50)
            elif inventario_tipo == "alto":
                cantidad_disponible = random.randint(51, 80)
            else:  # muy_alto
                cantidad_disponible = random.randint(81, 150)

            cantidad_reservada = random.randint(0, int(cantidad_disponible * 0.5))

            Inventario.objects.create(
                productos=producto,
                bodegas=bodega,
                cantidad_disponible=cantidad_disponible,
                cantidad_reservada=cantidad_reservada,
                ultima_actualizacion=datetime.now() - timedelta(days=random.randint(0, 30))
            )

def run():
    create_productos()
    create_bodegas()
    create_inventario()
    print("✅ Datos colombianos de dotaciones insertados correctamente.")

if __name__ == "__main__":
    run()