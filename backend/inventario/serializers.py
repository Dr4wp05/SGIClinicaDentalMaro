from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Sum
from django.db.models.functions import Coalesce

from .models import Producto, Lote, Categoria, MovimientoInventario, Proveedor, OrdenCompra, PerfilUsuario

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Inyectar claims personalizados en el Token JWT
        perfil = getattr(user, 'perfil', None)
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['rol'] = perfil.rol if perfil else 'ASISTENTE'
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        perfil = getattr(self.user, 'perfil', None)
        
        # Inyectar respuesta en el cuerpo de la petición POST /api/token/
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'rol': perfil.rol if perfil else 'ASISTENTE'
        }
        return data

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

class LoteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    class Meta:
        model = Lote
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor_habitual.nombre_fantasia')
    stock_total = serializers.SerializerMethodField()
    lotes = LoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Producto
        fields = '__all__'

    def get_stock_total(self, obj):
        return obj.lotes.aggregate(total=Coalesce(Sum('cantidad_actual'), 0))['total']

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    lote_detalle = LoteSerializer(source='lote', read_only=True)
    class Meta:
        model = MovimientoInventario
        fields = '__all__'

class OrdenCompraSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre_fantasia')
    creado_por_nombre = serializers.ReadOnlyField(source='creado_por.user.username')
    lotes = LoteSerializer(many=True, read_only=True)
    class Meta:
        model = OrdenCompra
        fields = '__all__'
