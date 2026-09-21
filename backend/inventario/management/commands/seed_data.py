from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventario.models import Categoria, Producto, Lote

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba reales para la Clínica'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando base de datos...")

        # 1. Categorías
        cat_anestesia, _ = Categoria.objects.get_or_create(nombre="Anestesia y Quirúrgicos")
        cat_restauracion, _ = Categoria.objects.get_or_create(nombre="Restauración y Estética")
        cat_proteccion, _ = Categoria.objects.get_or_create(nombre="Protección e Higiene")

        # 2. Productos
        p1, _ = Producto.objects.get_or_create(
            codigo_barras="7891001",
            defaults={'nombre': 'Lidocaína 2% con Epinefrina', 'categoria': cat_anestesia, 'stock_minimo': 20}
        )
        p2, _ = Producto.objects.get_or_create(
            codigo_barras="7891002",
            defaults={'nombre': 'Resina Compuesta A2 Filtek', 'categoria': cat_restauracion, 'stock_minimo': 10}
        )
        p3, _ = Producto.objects.get_or_create(
            codigo_barras="7891003",
            defaults={'nombre': 'Guantes de Nitrilo Talla M (Caja 100u)', 'categoria': cat_proteccion, 'stock_minimo': 50}
        )
        p4, _ = Producto.objects.get_or_create(
            codigo_barras="7891004",
            defaults={'nombre': 'Agujas Cortas 30G (Caja 100u)', 'categoria': cat_anestesia, 'stock_minimo': 15}
        )

        # 3. Lotes con fechas dinámicas
        hoy = timezone.now().date()

        # Lotes Normales
        Lote.objects.get_or_create(
            numero_lote="LOT-2026-A1",
            producto=p1,
            defaults={
                'cantidad_inicial': 100,
                'cantidad_actual': 100,
                'fecha_compra': hoy,
                'fecha_vencimiento': hoy + timedelta(days=365)
            }
        )
        Lote.objects.get_or_create(
            numero_lote="LOT-2026-B1",
            producto=p3,
            defaults={
                'cantidad_inicial': 150,
                'cantidad_actual': 150,
                'fecha_compra': hoy,
                'fecha_vencimiento': hoy + timedelta(days=500)
            }
        )

        # Lote Próximo a Vencer (dentro de los próximos 30 días)
        Lote.objects.get_or_create(
            numero_lote="LOT-VENC-01",
            producto=p2,
            defaults={
                'cantidad_inicial': 15,
                'cantidad_actual': 15,
                'fecha_compra': hoy - timedelta(days=30),
                'fecha_vencimiento': hoy + timedelta(days=12)
            }
        )

        # Producto con Stock Crítico (sólo 3 unidades cuando el mínimo es 15)
        Lote.objects.get_or_create(
            numero_lote="LOT-CRIT-01",
            producto=p4,
            defaults={
                'cantidad_inicial': 3,
                'cantidad_actual': 3,
                'fecha_compra': hoy - timedelta(days=10),
                'fecha_vencimiento': hoy + timedelta(days=120)
            }
        )

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
