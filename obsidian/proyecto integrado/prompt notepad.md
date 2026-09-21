urls:
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from inventario.views import (
    ProductoViewSet, LoteViewSet, CategoriaViewSet, ProveedorViewSet,
    MovimientoViewSet, AlertaViewSet, OrdenCompraViewSet, CustomTokenObtainPairView,
    usuario_actual_view
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'lotes', LoteViewSet)
router.register(r'categorias', CategoriaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'movimientos', MovimientoViewSet)
router.register(r'ordenes-compra', OrdenCompraViewSet)
router.register(r'alertas', AlertaViewSet, basename='alertas')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/usuarios/me/', usuario_actual_view, name='usuario_actual'),
    path('api/', include(router.urls)),
]

views:
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

insumos:
<template>
  <div class="insumos-container p-6 bg-slate-50 min-h-screen">
    <!-- Cabecera -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Gestión de Insumos y Lotes</h1>
        <p class="text-slate-500 text-sm">Administración del catálogo de productos y recepciones de stock</p>
      </div>
      <div class="flex gap-3">
        <button 
          @click="abrirModalLote()" 
          class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-sm cursor-pointer"
        >
          <span>+</span> Ingresar Lote
        </button>
        <button 
          @click="abrirModalProducto()" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-sm cursor-pointer"
        >
          <span>+</span> Nuevo Insumo
        </button>
      </div>
    </div>

    <!-- Barra de Búsqueda y Filtros -->
    <div class="bg-white p-4 rounded-xl shadow-sm mb-6 flex flex-wrap gap-4 items-center border border-slate-200">
      <input 
        v-model="filtroBusqueda" 
        type="text" 
        placeholder="Buscar por nombre, código o marca..." 
        class="flex-1 min-w-[250px] border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select 
        v-model="filtroCategoria" 
        class="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      >
        <option value="">Todas las Categorías</option>
        <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">
          {{ cat.nombre }}
        </option>
      </select>
    </div>

    <!-- Mensaje de Carga / Error -->
    <div v-if="store.loading && !store.productos.length" class="text-center py-10 text-slate-500">Cargando inventario...</div>
    <div v-else-if="store.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ store.error }}
    </div>

    <!-- Tabla de Insumos -->
    <div v-else class="bg-white rounded-xl shadow-sm overflow-hidden border border-slate-200">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-100 text-slate-600 text-xs uppercase tracking-wider border-b border-slate-200">
            <th class="py-3 px-4">Código</th>
            <th class="py-3 px-4">Insumo</th>
            <th class="py-3 px-4">Categoría</th>
            <th class="py-3 px-4">U. Medida</th>
            <th class="py-3 px-4 text-center">Stock Actual</th>
            <th class="py-3 px-4 text-center">Stock Mínimo</th>
            <th class="py-3 px-4 text-center">Estado Stock</th>
            <th class="py-3 px-4 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          <template v-for="prod in productosFiltrados" :key="prod.id">
            <tr class="hover:bg-slate-50 transition">
              <td class="py-3 px-4 font-mono text-xs text-slate-500">{{ prod.codigo_barras }}</td>
              <td class="py-3 px-4 font-semibold text-slate-800">
                {{ prod.nombre }}
                <span v-if="prod.marca" class="block text-xs font-normal text-slate-400">{{ prod.marca }}</span>
              </td>
              <td class="py-3 px-4 text-slate-600">{{ prod.categoria_nombre || 'Sin Categoría' }}</td>
              <td class="py-3 px-4 text-slate-600 capitalize">{{ prod.unidad_medida }}</td>
              <td class="py-3 px-4 text-center font-bold text-slate-800">{{ prod.stock_total }}</td>
              <td class="py-3 px-4 text-center text-slate-500">{{ prod.stock_minimo }}</td>
              <td class="py-3 px-4 text-center">
                <span 
                  :class="prod.stock_total <= prod.stock_minimo ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'"
                  class="px-2 py-1 rounded-full text-xs font-semibold"
                >
                  {{ prod.stock_total <= prod.stock_minimo ? 'Crítico' : 'Normal' }}
                </span>
              </td>
              <td class="py-3 px-4 text-right flex justify-end gap-2 items-center">
                <button 
                  @click="toggleDetalleLotes(prod.id)" 
                  class="text-blue-600 hover:text-blue-800 text-xs font-medium underline cursor-pointer"
                >
                  {{ loteDesplegado === prod.id ? 'Ocultar Lotes' : 'Ver Lotes (' + (prod.lotes ? prod.lotes.length : 0) + ')' }}
                </button>
                <button 
                  @click="abrirModalLote(prod)" 
                  class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-2 py-1 rounded border border-slate-300 cursor-pointer"
                >
                  + Lote
                </button>
              </td>
            </tr>

            <!-- Desglose de Lotes del Producto -->
            <tr v-if="loteDesplegado === prod.id" class="bg-slate-50/70 border-b border-slate-200">
              <td colspan="8" class="p-4">
                <div class="bg-white p-3 rounded-lg border border-slate-200 shadow-inner">
                  <h4 class="text-xs font-bold text-slate-700 uppercase mb-2">Detalle de Lotes Asociados</h4>
                  <table v-if="prod.lotes && prod.lotes.length" class="w-full text-xs text-left">
                    <thead>
                      <tr class="text-slate-400 border-b border-slate-100">
                        <th class="py-1">Nº Lote</th>
                        <th class="py-1">F. Compra</th>
                        <th class="py-1">F. Vencimiento</th>
                        <th class="py-1">Costo Unit.</th>
                        <th class="py-1 text-center">Cant. Inicial</th>
                        <th class="py-1 text-center">Cant. Actual</th>
                        <th class="py-1 text-center">Agotado</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="lote in prod.lotes" :key="lote.id" class="border-b border-slate-50">
                        <td class="py-1.5 font-mono text-slate-600">{{ lote.numero_lote }}</td>
                        <td class="py-1.5 text-slate-600">{{ lote.fecha_compra }}</td>
                        <td class="py-1.5 text-slate-600 font-medium" :class="esPorVencer(lote.fecha_vencimiento) ? 'text-amber-600 font-bold' : ''">
                          {{ lote.fecha_vencimiento }}
                        </td>
                        <td class="py-1.5 text-slate-600">${{ Number(lote.costo_unitario).toLocaleString() }}</td>
                        <td class="py-1.5 text-center text-slate-500">{{ lote.cantidad_inicial }}</td>
                        <td class="py-1.5 text-center font-bold text-slate-700">{{ lote.cantidad_actual }}</td>
                        <td class="py-1.5 text-center">
                          <span :class="lote.agotado ? 'text-red-500 font-semibold' : 'text-emerald-500 font-semibold'">
                            {{ lote.agotado ? 'Sí' : 'No' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p v-else class="text-xs text-slate-400 italic">No existen lotes registrados para este insumo.</p>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- MODAL NUEVO PRODUCTO -->
    <div v-if="modalProductoOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Crear Nuevo Insumo</h2>
        
        <form @submit.prevent="guardarProducto" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Código de Barras *</label>
              <input v-model="formProducto.codigo_barras" type="text" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Nombre Insumo *</label>
              <input v-model="formProducto.nombre" type="text" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Marca</label>
              <input v-model="formProducto.marca" type="text" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Categoría *</label>
              <select v-model="formProducto.categoria" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option value="" disabled>Seleccione Categoria</option>
                <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">{{ cat.nombre }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Proveedor Habitual</label>
              <select v-model="formProducto.proveedor_habitual" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option :value="null">Ninguno / Sin definir</option>
                <option v-for="prov in store.proveedores" :key="prov.id" :value="prov.id">{{ prov.nombre_fantasia }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Unidad de Medida *</label>
              <select v-model="formProducto.unidad_medida" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
                <option value="caja">Caja</option>
                <option value="cartucho">Cartucho</option>
                <option value="frasco">Frasco</option>
                <option value="tubo">Tubo</option>
                <option value="kit">Kit</option>
                <option value="unidad">Unidad</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Stock Mínimo Crítico *</label>
            <input v-model.number="formProducto.stock_minimo" type="number" min="0" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
          </div>

          <div v-if="errorForm" class="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded">
            {{ errorForm }}
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" @click="modalProductoOpen = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="store.loading" class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {{ store.loading ? 'Guardando...' : 'Guardar Insumo' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL NUEVO LOTE -->
    <div v-if="modalLoteOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Ingresar Nuevo Lote de Stock</h2>
        
        <form @submit.prevent="guardarLote" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Producto / Insumo *</label>
            <select v-model="formLote.producto" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm bg-white">
              <option value="" disabled>Seleccionar Producto</option>
              <option v-for="prod in store.productos" :key="prod.id" :value="prod.id">
                {{ prod.nombre }} ({{ prod.codigo_barras }})
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Número de Lote *</label>
              <input v-model="formLote.numero_lote" type="text" placeholder="EJ: L-2026-001" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Cantidad Inicial *</label>
              <input v-model.number="formLote.cantidad_inicial" type="number" min="1" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Fecha Compra *</label>
              <input v-model="formLote.fecha_compra" type="date" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">Fecha Vencimiento *</label>
              <input v-model="formLote.fecha_vencimiento" type="date" required class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Costo Unitario ($)</label>
            <input v-model.number="formLote.costo_unitario" type="number" step="0.01" min="0" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
          </div>

          <div v-if="errorForm" class="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded">
            {{ errorForm }}
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" @click="modalLoteOpen = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="store.loading" class="px-4 py-2 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50 cursor-pointer">
              {{ store.loading ? 'Guardando...' : 'Guardar Lote' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()

const filtroBusqueda = ref('')
const filtroCategoria = ref('')
const loteDesplegado = ref(null)

const modalProductoOpen = ref(false)
const modalLoteOpen = ref(false)
const errorForm = ref('')

const formProducto = ref({
  codigo_barras: '',
  nombre: '',
  marca: '',
  categoria: '',
  proveedor_habitual: null,
  unidad_medida: 'unidad',
  stock_minimo: 5
})

const formLote = ref({
  producto: '',
  numero_lote: '',
  fecha_compra: new Date().toISOString().split('T')[0],
  fecha_vencimiento: '',
  costo_unitario: 0,
  cantidad_inicial: 10
})

onMounted(async () => {
  await Promise.all([
    store.fetchProductos(),
    store.fetchCategorias(),
    store.fetchProveedores()
  ])
})

const productosFiltrados = computed(() => {
  return store.productos.filter(p => {
    const coincideNombre = p.nombre.toLowerCase().includes(filtroBusqueda.value.toLowerCase()) ||
                          p.codigo_barras.toLowerCase().includes(filtroBusqueda.value.toLowerCase()) ||
                          (p.marca && p.marca.toLowerCase().includes(filtroBusqueda.value.toLowerCase()))
    
    const coincideCat = filtroCategoria.value === '' || p.categoria === Number(filtroCategoria.value)
    
    return coincideNombre && coincideCat
  })
})

const toggleDetalleLotes = (id) => {
  loteDesplegado.value = loteDesplegado.value === id ? null : id
}

const abrirModalProducto = () => {
  errorForm.value = ''
  formProducto.value = {
    codigo_barras: '',
    nombre: '',
    marca: '',
    categoria: store.categorias.length ? store.categorias[0].id : '',
    proveedor_habitual: null,
    unidad_medida: 'unidad',
    stock_minimo: 5
  }
  modalProductoOpen.value = true
}

const abrirModalLote = (producto = null) => {
  errorForm.value = ''
  formLote.value = {
    producto: producto ? producto.id : (store.productos.length ? store.productos[0].id : ''),
    numero_lote: '',
    fecha_compra: new Date().toISOString().split('T')[0],
    fecha_vencimiento: '',
    costo_unitario: 0,
    cantidad_inicial: 10
  }
  modalLoteOpen.value = true
}

const guardarProducto = async () => {
  try {
    errorForm.value = ''
    await store.crearProducto(formProducto.value)
    modalProductoOpen.value = false
  } catch (err) {
    errorForm.value = err.message || 'Error al guardar el insumo'
  }
}

const guardarLote = async () => {
  try {
    errorForm.value = ''
    await store.crearLote(formLote.value)
    modalLoteOpen.value = false
  } catch (err) {
    errorForm.value = err.message || 'Error al guardar el lote'
  }
}

const esPorVencer = (fechaStr) => {
  if (!fechaStr) return false
  const fecha = new Date(fechaStr)
  const hoy = new Date()
  const limite = new Date()
  limite.setDate(hoy.getDate() + 30)
  return fecha >= hoy && fecha <= limite
}
</script>

movimientosview:
<template>
  <div class="p-8 space-y-6 bg-slate-50 min-h-screen w-full">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Movimientos de Inventario</h1>
        <p class="text-slate-500 text-sm">Historial de entradas, salidas y mermas - Clínica Dental Maró</p>
      </div>
      <button 
        @click="abrirModal = true"
        class="inline-flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium text-sm transition-colors shadow-sm cursor-pointer"
      >
        <ArrowLeftRight class="w-4 h-4" />
        Registrar Movimiento
      </button>
    </div>

    <!-- Indicador de Carga -->
    <div v-if="store.loading" class="text-slate-500 text-sm font-medium">
      Cargando historial de movimientos...
    </div>

    <!-- Tabla Histórica -->
    <div v-else class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-600">
          <thead class="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-xs">
            <tr>
              <th class="px-6 py-4">Fecha y Hora</th>
              <th class="px-6 py-4">Tipo</th>
              <th class="px-6 py-4">Insumo</th>
              <th class="px-6 py-4">Lote</th>
              <th class="px-6 py-4">Cantidad</th>
              <th class="px-6 py-4">Detalle / Motivo</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="m in store.movimientos" :key="m.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 text-xs font-mono text-slate-500">
                {{ formatearFecha(m.fecha_hora) }}
              </td>
              <td class="px-6 py-4">
                <span :class="getBadgeClass(m.tipo_movimiento)" class="px-2.5 py-1 rounded-full text-xs font-semibold">
                  {{ m.tipo_movimiento }}
                </span>
              </td>
              <td class="px-6 py-4 font-semibold text-slate-800">
                {{ m.lote_detalle?.producto_nombre || '—' }}
              </td>
              <td class="px-6 py-4 text-xs font-mono text-slate-600">
                {{ m.lote_detalle?.numero_lote || m.lote }}
              </td>
              <td class="px-6 py-4 font-bold" :class="m.tipo_movimiento === 'ENTRADA' ? 'text-teal-600' : 'text-rose-600'">
                {{ m.tipo_movimiento === 'ENTRADA' ? '+' : '-' }}{{ m.cantidad }}
              </td>
              <td class="px-6 py-4 text-xs text-slate-500">
                {{ m.motivo_perdida || 'Sin especificación' }}
              </td>
            </tr>
            <tr v-if="store.movimientos.length === 0">
              <td colspan="6" class="px-6 py-8 text-center text-slate-400">
                No hay movimientos registrados en la bitácora.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Registrar Movimiento -->
    <div v-if="abrirModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-lg font-bold text-slate-800">Nuevo Movimiento</h3>
          <button @click="cerrarModal" class="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer">&times;</button>
        </div>

        <form @submit.prevent="guardarMovimiento" class="space-y-4">
          <!-- Seleccionar Producto -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Producto</label>
            <select v-model="productoSeleccionadoId" @change="alCambiarProducto" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none">
              <option value="" disabled>Seleccione un producto...</option>
              <option v-for="p in store.productos" :key="p.id" :value="p.id">
                {{ p.nombre }}
              </option>
            </select>
          </div>

          <!-- Seleccionar Lote -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Lote de Origen/Destino</label>
            <select v-model="form.lote" :disabled="!lotesDisponibles.length" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none disabled:bg-slate-100">
              <option value="" disabled>Seleccione un lote...</option>
              <option v-for="l in lotesDisponibles" :key="l.id" :value="l.id">
                Lote: {{ l.numero_lote }} (Disponible: {{ l.cantidad_actual }})
              </option>
            </select>
          </div>

          <!-- Tipo Movimiento -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Tipo de Operación</label>
            <select v-model="form.tipo_movimiento" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none">
              <option value="CONSUMO">Consumo en Procedimiento / Box</option>
              <option value="MERMA_PERDIDA">Pérdida / Extravío / Dañado</option>
              <option value="MERMA_VENCIMIENTO">Vencimiento</option>
              <option value="ENTRADA">Entrada / Reposición</option>
            </select>
          </div>

          <!-- Cantidad -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Cantidad</label>
            <input type="number" min="1" v-model.number="form.cantidad" required class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none" />
          </div>

          <!-- Motivo -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 uppercase mb-1">Observación / Motivo</label>
            <textarea v-model="form.motivo_perdida" rows="2" placeholder="Detalles opcionales..." class="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-none"></textarea>
          </div>

          <!-- Mensaje Error Form -->
          <p v-if="errorForm" class="text-xs text-rose-600 font-medium">{{ errorForm }}</p>

          <!-- Botones -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <button type="button" @click="cerrarModal" class="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer">Cancelar</button>
            <button type="submit" :disabled="guardando" class="px-4 py-2 text-sm font-medium bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors cursor-pointer">
              {{ guardando ? 'Guardando...' : 'Confirmar Registro' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ArrowLeftRight } from 'lucide-vue-next'
import { useInventoryStore } from '@/stores/inventoryStore'

const store = useInventoryStore()
const abrirModal = ref(false)
const guardando = ref(false)
const errorForm = ref('')

const productoSeleccionadoId = ref('')
const form = ref({
  lote: '',
  tipo_movimiento: 'CONSUMO',
  cantidad: 1,
  motivo_perdida: ''
})

const lotesDisponibles = computed(() => {
  if (!productoSeleccionadoId.value) return []
  const prod = store.productos.find(p => p.id === productoSeleccionadoId.value)
  return prod ? prod.lotes || [] : []
})

const alCambiarProducto = () => {
  form.value.lote = ''
}

const cerrarModal = () => {
  abrirModal.value = false
  errorForm.value = ''
  productoSeleccionadoId.value = ''
  form.value = { lote: '', tipo_movimiento: 'CONSUMO', cantidad: 1, motivo_perdida: '' }
}

const guardarMovimiento = async () => {
  errorForm.value = ''
  guardando.value = true
  try {
    await store.registrarMovimiento(form.value)
    cerrarModal()
  } catch (err) {
    errorForm.value = err.message
  } finally {
    guardando.value = false
  }
}

const formatearFecha = (strFecha) => {
  if (!strFecha) return '—'
  return new Date(strFecha).toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const getBadgeClass = (tipo) => {
  switch (tipo) {
    case 'ENTRADA': return 'bg-teal-100 text-teal-800'
    case 'CONSUMO': return 'bg-sky-100 text-sky-800'
    case 'MERMA_PERDIDA': return 'bg-rose-100 text-rose-800'
    case 'MERMA_VENCIMIENTO': return 'bg-amber-100 text-amber-800'
    default: return 'bg-slate-100 text-slate-800'
  }
}

onMounted(() => {
  store.fetchMovimientos()
  store.fetchProductos()
})
</script>

