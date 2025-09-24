import os
import django
import random
from faker import Faker

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoArquisoft.settings')
django.setup()

# Importar modelos
from core.models import Cliente, Producto, Bodega, Inventario

faker = Faker()

# Crear clientes
def create_clientes(n=10):
    for _ in range(n):
        Cliente.objects.create(
            nombre=faker.name(),
            info_pago=faker.credit_card_number()
        )

# Crear productos
def create_productos(n=10):
    for _ in range(n):
        Producto.objects.create(
            codigo_barras=faker.ean13(),
            tipo=random.choice(['Electrónico', 'Ropa', 'Comida']),
            peso=round(random.uniform(0.5, 10.0), 2),
            volumen=round(random.uniform(0.1, 5.0), 2),
            codigo=faker.bothify(text='PRD-####')
        )

# Crear bodegas
def create_bodegas(n=3):
    for _ in range(n):
        Bodega.objects.create(
            codigo=faker.bothify(text='BOD###'),
            nombre=faker.company(),
            ciudad=faker.city(),
            direccion=faker.address(),
            capacidad=round(random.uniform(100.0, 1000.0), 2)
        )

# Crear inventario (productos en bodegas)
def create_inventario():
    bodegas = list(Bodega.objects.all())
    productos = list(Producto.objects.all())

    for bodega in bodegas:
        productos_sample = random.sample(productos, k=min(5, len(productos)))
        for producto in productos_sample:
            Inventario.objects.create(
                productos=producto,
                bodegas=bodega,
                cantidad_disponible=random.randint(10, 100),
                cantidad_reservada=random.randint(0, 50),
                ultima_actualizacion=faker.date_time_this_year()
            )

# Ejecutar todo
def run():
    create_clientes(10)
    create_productos(20)
    create_bodegas(5)
    create_inventario()
    print("✅ Mock data inserted successfully.")
    
if __name__ == "__main__":
    run()