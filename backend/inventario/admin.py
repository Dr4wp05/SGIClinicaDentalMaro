from django.contrib import admin
from .models import (
    PerfilUsuario, Categoria, Proveedor, Producto, 
    OrdenCompra, Lote, Ubicacion, MovimientoInventario
)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'rut', 'telefono')
    list_filter = ('rol',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre_fantasia', 'rut_empresa', 'contacto_nombre', 'telefono', 'email')
    search_fields = ('nombre_fantasia', 'rut_empresa')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'codigo_barras', 'categoria', 'unidad_medida', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo', 'unidad_medida')
    search_fields = ('nombre', 'codigo_barras', 'marca')

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('numero_lote', 'producto', 'fecha_vencimiento', 'cantidad_actual', 'costo_unitario', 'agotado')
    list_filter = ('agotado', 'fecha_vencimiento')
    search_fields = ('numero_lote', 'producto__nombre')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'tipo_movimiento', 'lote', 'cantidad', 'usuario', 'origen', 'destino')
    list_filter = ('tipo_movimiento', 'fecha_hora')
    readonly_fields = ('fecha_hora',)

admin.site.register(OrdenCompra)
admin.site.register(Ubicacion)
