from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import pandas as pd
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Producto, Lote, Categoria, MovimientoInventario, Proveedor, PerfilUsuario, OrdenCompra
from .serializers import (
    ProductoSerializer, LoteSerializer, CategoriaSerializer,
    MovimientoInventarioSerializer, ProveedorSerializer, OrdenCompraSerializer,
    CustomTokenObtainPairSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuario_actual_view(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'rol': perfil.rol if perfil else 'ASISTENTE'
    })

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(activo=True)
    serializer_class = ProductoSerializer

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all().order_by('-fecha_hora')
    serializer_class = MovimientoInventarioSerializer

    def create(self, request, *args, **kwargs):
        lote_id = request.data.get('lote')
        tipo_movimiento = request.data.get('tipo_movimiento')
        cantidad = int(request.data.get('cantidad', 0))
        motivo_perdida = request.data.get('motivo_perdida', '')

        if cantidad <= 0:
            return Response({'error': 'La cantidad debe ser mayor a 0.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                lote = Lote.objects.select_for_update().get(id=lote_id)
            except Lote.DoesNotExist:
                return Response({'error': 'El lote especificado no existe.'}, status=status.HTTP_404_NOT_FOUND)

            perfil_usuario = getattr(request.user, 'perfil', None) or PerfilUsuario.objects.first()

            if not perfil_usuario:
                user_def, _ = User.objects.get_or_create(
                    username='sistema_maro', 
                    defaults={'first_name': 'Sistema', 'last_name': 'Maró'}
                )
                perfil_usuario, _ = PerfilUsuario.objects.get_or_create(
                    user=user_def,
                    defaults={'rol': 'ADMINISTRADOR'}
                )

            if tipo_movimiento in ['CONSUMO', 'MERMA_PERDIDA', 'MERMA_VENCIMIENTO']:
                if lote.cantidad_actual < cantidad:
                    return Response({
                        'error': f'Stock insuficiente en lote {lote.numero_lote}. Disponible: {lote.cantidad_actual}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                lote.cantidad_actual -= cantidad
                if lote.cantidad_actual == 0:
                    lote.agotado = True
                    lote.fecha_agotado = timezone.now()

            elif tipo_movimiento in ['ENTRADA', 'AJUSTE']:
                lote.cantidad_actual += cantidad
                if lote.cantidad_actual > 0:
                    lote.agotado = False
                    lote.fecha_agotado = None

            lote.save()

            movimiento = MovimientoInventario.objects.create(
                lote=lote,
                usuario=perfil_usuario,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                motivo_perdida=motivo_perdida
            )

            serializer = self.get_serializer(movimiento)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrdenCompraViewSet(viewsets.ModelViewSet):
    queryset = OrdenCompra.objects.all().order_by('-fecha_creacion')
    serializer_class = OrdenCompraSerializer

    @action(detail=False, methods=['post'], url_path='generar-sugerencias')
    def generar_sugerencias(self, request):
        productos = Producto.objects.filter(activo=True)
        criticos_por_proveedor = {}

        proveedor_def, _ = Proveedor.objects.get_or_create(
            rut_empresa="77.777.777-7",
            defaults={
                'nombre_fantasia': 'Proveedor Central Clínico',
                'contacto_nombre': 'Ejecutivo de Ventas',
                'email': 'ventas@proveedor.cl',
                'telefono': '+56912345678'
            }
        )

        for p in productos:
            stock_total = p.lotes.aggregate(total=Coalesce(Sum('cantidad_actual'), 0))['total']
            
            if stock_total <= p.stock_minimo:
                prov = p.proveedor_habitual or proveedor_def
                if prov.id not in criticos_por_proveedor:
                    criticos_por_proveedor[prov.id] = []
                
                criticos_por_proveedor[prov.id].append({
                    'producto': p,
                    'cantidad_sugerida': max(p.stock_minimo * 2, 10)
                })

        if not criticos_por_proveedor:
            return Response({
                'error': 'No hay productos en stock crítico para generar sugerencias.'
            }, status=status.HTTP_400_BAD_REQUEST)

        perfil_usuario = getattr(request.user, 'perfil', None) or PerfilUsuario.objects.first()
        if not perfil_usuario:
            user_def, _ = User.objects.get_or_create(username='sistema_maro')
            perfil_usuario, _ = PerfilUsuario.objects.get_or_create(user=user_def, defaults={'rol': 'ADMINISTRADOR'})

        ordenes_creadas = []
        with transaction.atomic():
            for prov_id, items in criticos_por_proveedor.items():
                orden = OrdenCompra.objects.create(
                    proveedor_id=prov_id,
                    creado_por=perfil_usuario,
                    estado='borrador'
                )
                for item in items:
                    prod = item['producto']
                    cant = item['cantidad_sugerida']
                    Lote.objects.create(
                        producto=prod,
                        orden_compra=orden,
                        numero_lote=f"PENDIENTE-OC-{orden.id}",
                        fecha_compra=timezone.now().date(),
                        fecha_vencimiento=timezone.now().date() + timezone.timedelta(days=365),
                        costo_unitario=0.0,
                        cantidad_inicial=cant,
                        cantidad_actual=0,
                        agotado=True
                    )
                ordenes_creadas.append(orden.id)

        ordenes = OrdenCompra.objects.filter(id__in=ordenes_creadas)
        serializer = self.get_serializer(ordenes, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        orden = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado not in ['borrador', 'enviada', 'recibida', 'cancelada']:
            return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            orden.estado = nuevo_estado
            
            if nuevo_estado == 'enviada':
                destino_correo = "alonsorodriguezcaceres@gmail.com"
                
                items_detalle = ""
                for lote in orden.lotes.all():
                    items_detalle += f" - {lote.producto.nombre}: {lote.cantidad_inicial} unidades\n"

                asunto = f"[SIMULACIÓN] Nueva Orden de Compra #{orden.id} - Clínica Dental"
                mensaje = f"""
Estimado Proveedor ({orden.proveedor.nombre_fantasia}),
Se ha generado una nueva Orden de Compra por quiebre/stock crítico en nuestro inventario.
Detalles de la Orden #{orden.id}:

Fecha de emisión: {orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')}
Proveedor de destino: {orden.proveedor.nombre_fantasia}
Creado por: {orden.creado_por.user.get_full_name() or orden.creado_por.user.username}
Insumos solicitados:

{items_detalle}
Por favor confirmar la recepción y procesar el despacho a la brevedad.
Atentamente,
Sistema de Gestión e Inventario Clínico MARO
"""
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'no-reply@maroclinica.cl',
                    [destino_correo],
                    fail_silently=False,
                )
            elif nuevo_estado == 'recibida':
                orden.fecha_recepcion = timezone.now()
                for lote in orden.lotes.all():
                    if lote.cantidad_actual == 0:
                        lote.cantidad_actual = lote.cantidad_inicial
                        lote.agotado = False
                        lote.numero_lote = f"LOTE-OC{orden.id}-{lote.id}"
                        lote.save()

                        perfil_usuario = getattr(request.user, 'perfil', None) or PerfilUsuario.objects.first()
                        MovimientoInventario.objects.create(
                            lote=lote,
                            usuario=perfil_usuario,
                            tipo_movimiento='ENTRADA',
                            cantidad=lote.cantidad_inicial,
                            motivo_perdida=f"Recepción de Orden de Compra #{orden.id}"
                        )
            orden.save()

        serializer = self.get_serializer(orden)
        return Response(serializer.data)

class AlertaViewSet(viewsets.ViewSet):
    def _obtener_ids_stock_critico(self):
        productos = Producto.objects.filter(activo=True)
        criticos_ids = []
        for p in productos:
            total_stock = p.lotes.aggregate(total=Coalesce(Sum('cantidad_actual'), 0))['total']
            if total_stock <= p.stock_minimo:
                criticos_ids.append(p.id)
        return criticos_ids

    @action(detail=False, methods=['get'], url_path='stock-critico')
    def stock_critico(self, request):
        ids = self._obtener_ids_stock_critico()
        productos = Producto.objects.filter(id__in=ids)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def vencimientos(self, request):
        hoy = timezone.now().date()
        limite = hoy + timezone.timedelta(days=30)
        lotes = Lote.objects.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite)
        serializer = LoteSerializer(lotes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        hoy = timezone.now().date()
        limite = hoy + timezone.timedelta(days=30)
        stock_critico_count = len(self._obtener_ids_stock_critico())
        por_vencer_count = Lote.objects.filter(
            fecha_vencimiento__gte=hoy, 
            fecha_vencimiento__lte=limite
        ).count()

        return Response({
            "stock_critico": stock_critico_count,
            "por_vencer": por_vencer_count,
            "total_alertas": stock_critico_count + por_vencer_count
        })

class ReportesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='financiero')
    def financiero(self, request):
        lotes_activos = Lote.objects.filter(cantidad_actual__gt=0)
        capital_total = sum(lote.cantidad_actual * float(lote.costo_unitario) for lote in lotes_activos)

        movs_mermas = MovimientoInventario.objects.filter(
            tipo_movimiento__in=['MERMA_PERDIDA', 'MERMA_VENCIMIENTO']
        )
        total_mermas_costo = sum(m.cantidad * float(m.lote.costo_unitario) for m in movs_mermas)

        return Response({
            'capital_inmovilizado': capital_total,
            'perdida_mermas': total_mermas_costo,
            'total_lotes_activos': lotes_activos.count()
        })

    @action(detail=False, methods=['get'], url_path='rotacion')
    def rotacion(self, request):
        movs = MovimientoInventario.objects.filter(tipo_movimiento='CONSUMO')
        rotacion_dict = {}

        for m in movs:
            prod_nombre = m.lote.producto.nombre
            rotacion_dict[prod_nombre] = rotacion_dict.get(prod_nombre, 0) + m.cantidad

        ranking = [{'producto': k, 'total_consumido': v} for k, v in rotacion_dict.items()]
        ranking = sorted(ranking, key=lambda x: x['total_consumido'], reverse=True)[:5]

        return Response(ranking)

class CargaMasivaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='importar-excel')
    def importar_excel(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No se adjuntó ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj)
            # Columnas esperadas: Nombre, Categoria, StockMinimo, Lote, FechaVencimiento, CostoUnitario, CantidadInicial
            registrados = 0

            for _, row in df.iterrows():
                nombre_prod = str(row.get('Nombre', '')).strip()
                cat_nombre = str(row.get('Categoria', 'General')).strip()
                stock_min = int(row.get('StockMinimo', 5))

                num_lote = str(row.get('Lote', '')).strip()
                f_venc = row.get('FechaVencimiento')
                costo = float(row.get('CostoUnitario', 0))
                cant = int(row.get('CantidadInicial', 0))

                if not nombre_prod or not num_lote:
                    continue

                categoria, _ = Categoria.objects.get_or_create(nombre=cat_nombre)
                producto, _ = Producto.objects.get_or_create(
                    nombre=nombre_prod,
                    defaults={'categoria': categoria, 'stock_minimo': stock_min, 'activo': True}
                )

                Lote.objects.create(
                    producto=producto,
                    numero_lote=num_lote,
                    fecha_compra=timezone.now().date(),
                    fecha_vencimiento=pd.to_datetime(f_venc).date() if pd.notnull(f_venc) else timezone.now().date() + timezone.timedelta(days=365),
                    costo_unitario=costo,
                    cantidad_inicial=cant,
                    cantidad_actual=cant,
                    agotado=(cant == 0)
                )
                registrados += 1

            return Response({'message': f'Se importaron {registrados} registros correctamente.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Error al procesar archivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='exportar-inventario')
    def exportar_inventario(self, request):
        lotes = Lote.objects.all().select_related('producto', 'producto__categoria')
        data = []

        for l in lotes:
            data.append({
                'ID Lote': l.id,
                'Producto': l.producto.nombre,
                'Categoría': l.producto.categoria.nombre if l.producto.categoria else 'N/A',
                'N° Lote': l.numero_lote,
                'Cantidad Inicial': l.cantidad_inicial,
                'Cantidad Actual': l.cantidad_actual,
                'Costo Unitario ($)': l.costo_unitario,
                'Fecha Vencimiento': l.fecha_vencimiento.strftime('%d/%m/%Y') if l.fecha_vencimiento else '',
                'Agotado': 'Sí' if l.agotado else 'No'
            })

        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="inventario_clinica_maro.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stock Actual')

        return response
