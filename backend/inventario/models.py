from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    ROLES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('BODEGA', 'Encargado de Bodega'),
        ('DENTISTA', 'Dentista'),
        ('ASISTENTE', 'Asistente'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='ASISTENTE')
    rut = models.CharField(max_length=12, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

class Categoria(models.Model):

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    rut_empresa = models.CharField(max_length=12, unique=True)
    nombre_fantasia = models.CharField(max_length=150)
    contacto_nombre = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.nombre_fantasia

class Producto(models.Model):
    UNIDADES = [
        ('caja', 'Caja'),
        ('cartucho', 'Cartucho'),
        ('frasco', 'Frasco'),
        ('tubo', 'Tubo'),
        ('kit', 'Kit'),
        ('unidad', 'Unidad'),
    ]
    codigo_barras = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    proveedor_habitual = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_habituales')
    unidad_medida = models.CharField(max_length=20, choices=UNIDADES, default='unidad')
    stock_minimo = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.marca})"

class OrdenCompra(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada'),
    ]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='ordenes_compra')
    creado_por = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='ordenes_creadas')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OC #{self.id} - {self.proveedor.nombre_fantasia}"

class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    numero_lote = models.CharField(max_length=100)
    fecha_compra = models.DateField()
    fecha_vencimiento = models.DateField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_actual = models.PositiveIntegerField()
    agotado = models.BooleanField(default=False)
    fecha_agotado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.producto.nombre}"

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100) # ej: Bodega, Box 1, Box 2 Maró Kids

    def __str__(self):
        return self.nombre

class MovimientoInventario(models.Model):
    TIPOS = [
        ('ENTRADA', 'Entrada por compra'),
        ('TRASLADO', 'Traslado entre ubicaciones'),
        ('CONSUMO', 'Consumo en procedimiento'),
        ('MERMA_PERDIDA', 'Pérdida / Dañado / Extravío'),
        ('MERMA_VENCIMIENTO', 'Vencimiento'),
        ('AJUSTE', 'Ajuste de inventario'),
    ]
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='movimientos')
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='movimientos_registrados')
    origen = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_origen')
    destino = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_destino')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPOS)
    cantidad = models.IntegerField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    motivo_perdida = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_movimiento} ({self.cantidad}) - {self.lote.producto.nombre}"
