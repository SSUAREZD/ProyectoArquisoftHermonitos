import os
import django
import random
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoArquisoft.settings')
django.setup()

from core.models import Cliente, Producto, Bodega, Inventario, Pedido

faker = Faker()

def create_clientes(n=10):
    for _ in range(n):
        Cliente.objects.create(
            nombre=faker.name(),
            info_pago=faker.credit_card_number()
        )

def create_productos(n=10):
    for _ in range(n):
        Producto.objects.create(
            codigo_barras=faker.ean13(),
            tipo=random.choice(['Electronico', 'Ropa', 'Comida']),
            peso=random.uniform(0.5, 10.0),
            volumen=random.uniform(0.1, 5.0),
            codigo=faker.bothify(text='PRD-####')
        )

def create_bodegas(n=3):
    for _ in range(n):
        Bodega.objects.create(
            codigo=faker.bothify(text='BOD###'),
            nombre=faker.company(),
            ciudad=faker.city(),
            direccion=faker.address(),
            capacidad=random.uniform(100.0, 1000.0)
        )

def run():
    create_clientes(10)
    create_productos(20)
    create_bodegas(5)
    print("✅ Mock data inserted successfully.")