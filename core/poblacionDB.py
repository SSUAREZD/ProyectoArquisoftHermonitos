import os
import django
import random
from faker import Faker
from datetime import datetime, timedelta

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoArquisoft.settings')
django.setup()

# Importar modelos
from core.models import Cliente, Producto, Bodega, Inventario

faker = Faker()


def create_productos(n=20):
    for _ in range(n):
        Producto.objects.create(
            codigo_barras=faker.ean13(),
            tipo=random.choice(['Electrónico', 'Ropa', 'Comida']),
            peso=round(random.uniform(0.5, 10.0), 2),
            volumen=round(random.uniform(0.1, 5.0), 2),
            codigo=faker.bothify(text='PRD-####')
        )

def create_bodegas(n=5):
    for _ in range(n):
        Bodega.objects.create(
            codigo=faker.bothify(text='BOD###'),
            nombre=faker.company(),
            ciudad=faker.city(),
            direccion=faker.address(),
            capacidad=round(random.uniform(100.0, 1000.0), 2),
            latitud=random.uniform(4.5, 5.0),      
            longitud=random.uniform(-74.2, -73.9)  
        )

def create_inventario():
    bodegas = list(Bodega.objects.all())
    productos = list(Producto.objects.all())

    for bodega in bodegas:
        productos_sample = random.sample(productos, k=min(5, len(productos)))

        # Genera un tipo de inventario por bodega (bajo, medio, alto, muy alto)
        inventario_tipo = random.choice(["bajo", "medio", "alto", "muy_alto"])

        for producto in productos_sample:
            if inventario_tipo == "bajo":
                cantidad_disponible = random.randint(1, 20)
            elif inventario_tipo == "medio":
                cantidad_disponible = random.randint(21, 50)
            elif inventario_tipo == "alto":
                cantidad_disponible = random.randint(51, 80)
            else:  # muy_alto
                cantidad_disponible = random.randint(81, 100)

            cantidad_reservada = random.randint(0, int(cantidad_disponible * 0.5))

            Inventario.objects.create(
                productos=producto,
                bodegas=bodega,
                cantidad_disponible=cantidad_disponible,
                cantidad_reservada=cantidad_reservada,
                ultima_actualizacion=faker.date_time_this_year()
            )

def run():
    create_productos(20)
    create_bodegas(5)
    create_inventario()
    print("✅ Mock data inserted successfully.")

if __name__ == "__main__":
    run()