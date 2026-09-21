from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from inventario.views import (
    CustomTokenObtainPairView,
    usuario_actual_view,
    ProductoViewSet,
    LoteViewSet,
    CategoriaViewSet,
    ProveedorViewSet,
    MovimientoViewSet,
    OrdenCompraViewSet,
    AlertaViewSet,
    ReportesViewSet,
    CargaMasivaViewSet
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='productos')
router.register(r'lotes', LoteViewSet, basename='lotes')
router.register(r'categorias', CategoriaViewSet, basename='categorias')
router.register(r'proveedores', ProveedorViewSet, basename='proveedores')
router.register(r'movimientos', MovimientoViewSet, basename='movimientos')
router.register(r'ordenes-compra', OrdenCompraViewSet, basename='ordenes-compra')
router.register(r'alertas', AlertaViewSet, basename='alertas')
router.register(r'reportes', ReportesViewSet, basename='reportes')
router.register(r'carga-masiva', CargaMasivaViewSet, basename='carga-masiva')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/usuario-actual/', usuario_actual_view, name='usuario_actual'),
    path('api/', include(router.urls)),
]