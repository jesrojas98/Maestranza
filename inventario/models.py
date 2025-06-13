from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

from requests import request


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15, blank=True)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Sucursales"
    
    def __str__(self):
        return self.nombre

class Ubicacion(models.Model):
    TIPO_CHOICES = [
        ('pasillo', 'Pasillo'),
        ('estante', 'Estante'), 
        ('bodega', 'Bodega'),
        ('vitrina', 'Vitrina'),
        ('deposito', 'Depósito'),
        ('otro', 'Otro'),
    ]
    
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='ubicaciones')
    codigo = models.CharField(max_length=20)  # Ej: A-01, B-15, BOD-1
    nombre = models.CharField(max_length=100)  # Ej: Pasillo A - Estante 1
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='estante')
    descripcion = models.TextField(blank=True)
    capacidad_maxima = models.IntegerField(null=True, blank=True, help_text="Cantidad máxima de productos")
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['sucursal', 'codigo']
        verbose_name_plural = "Ubicaciones"
        ordering = ['sucursal', 'tipo', 'codigo']
    
    def __str__(self):
        return f"{self.sucursal.nombre} - {self.codigo}: {self.nombre}"
    
    def get_productos_count(self):
        """Cuenta productos en esta ubicación"""
        return Inventario.objects.filter(ubicacion_detallada=self).count()
    
    def get_capacidad_usada(self):
        """Obtiene la cantidad total de productos en esta ubicación"""
        total = Inventario.objects.filter(ubicacion_detallada=self).aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
        return total
    
    def get_porcentaje_ocupacion(self):
        """Obtiene el porcentaje de ocupación de la ubicación"""
        if not self.capacidad_maxima:
            return None
        usado = self.get_capacidad_usada()
        return round((usado / self.capacidad_maxima) * 100, 1) if self.capacidad_maxima > 0 else 0
    
    @property
    def esta_llena(self):
        """Verifica si la ubicación está al máximo de capacidad"""
        if not self.capacidad_maxima:
            return False
        return self.get_capacidad_usada() >= self.capacidad_maxima
    
    @property
    def necesita_atencion(self):
        """Verifica si la ubicación necesita atención (>80% ocupada)"""
        porcentaje = self.get_porcentaje_ocupacion()
        return porcentaje and porcentaje >= 80

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Proveedores"
    
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Color hex para UI
    
    class Meta:
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.nombre

class Etiqueta(models.Model):
    nombre = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#6c757d')
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    unidad_medida = models.CharField(max_length=20, default='unidad')
    stock_minimo = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    maneja_lotes = models.BooleanField(default=False)
    maneja_vencimiento = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(
        upload_to='productos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Imagen del Producto",
        help_text="Imagen del producto (JPG, PNG, máx. 5MB)"
    )
    precio = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio actual del producto"
    )
    precio_actualizado = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha de última actualización del precio"
    )

    class Meta:
        db_table = 'inventario_producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def get_precio_actual(self):
        """Retorna el precio actual del producto"""
        return self.precio

    
    def get_precio_formateado(self):
        """Retorna el precio formateado como string"""
        if self.precio:
            return f"${self.precio:,.2f}"
        return "Sin precio"
        
    def tiene_precio(self):
        """Verifica si el producto tiene precio asignado"""
        return self.precio is not None and self.precio > 0
        
    def actualizar_precio(self, nuevo_precio, save=True):
        """Actualiza el precio y la fecha de actualización"""
        from django.utils import timezone
        self.precio = nuevo_precio
        self.precio_actualizado = timezone.now()
        if save:
            self.save(update_fields=['precio', 'precio_actualizado'])

    def get_stock_total(self):
        """Obtiene el stock total de todas las sucursales"""
        return sum([inv.cantidad for inv in self.inventario_set.all()])

    def get_stock_sucursal(self, sucursal):
        """Obtiene el stock de una sucursal específica"""
        try:
            inventario = self.inventario_set.get(sucursal=sucursal)
            return inventario.cantidad
        except Inventario.DoesNotExist:
            return 0

    def get_imagen_url(self):
        """Retorna la URL de la imagen o una imagen por defecto"""
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return '/static/inventario/img/producto-default.png'
       
    def get_imagen_thumbnail(self):
        """Retorna la URL para thumbnail (se puede implementar con Pillow más adelante)"""
        return self.get_imagen_url()

    def delete_imagen_anterior(self):
        """Elimina la imagen anterior del sistema de archivos"""
        if self.imagen:
            if os.path.isfile(self.imagen.path):
                os.remove(self.imagen.path)

class Lote(models.Model):
    codigo = models.CharField(max_length=50)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['codigo', 'producto']
    
    def __str__(self):
        return f"Lote {self.codigo} - {self.producto.nombre}"
    
    @property
    def dias_vencimiento(self):
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - timezone.now().date()
            return delta.days
        return None
    
    @property
    def esta_vencido(self):
        if self.fecha_vencimiento:
            return self.fecha_vencimiento < timezone.now().date()
        return False

class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    ubicacion = models.CharField(max_length=100, blank=True)  # Mantener para compatibilidad
    ubicacion_detallada = models.ForeignKey(
        'Ubicacion', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Ubicación específica dentro de la sucursal"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['producto', 'sucursal']
        verbose_name_plural = "Inventarios"
    
    def __str__(self):
        ubicacion_str = self.get_ubicacion_completa()
        return f"{self.producto.nombre} - {self.sucursal.nombre} ({self.cantidad}) - {ubicacion_str}"
    
    @property
    def necesita_reposicion(self):
        return self.cantidad <= self.producto.stock_minimo
    
    def get_ubicacion_completa(self):
        """Obtiene la ubicación completa (detallada o general)"""
        if self.ubicacion_detallada:
            return str(self.ubicacion_detallada)
        elif self.ubicacion:
            return f"{self.sucursal.nombre} - {self.ubicacion}"
        else:
            return f"{self.sucursal.nombre} - Sin ubicación específica"
    
    def get_ubicacion_corta(self):
        """Obtiene una versión corta de la ubicación"""
        if self.ubicacion_detallada:
            return self.ubicacion_detallada.codigo
        elif self.ubicacion:
            return self.ubicacion
        else:
            return "N/A"

class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('transferencia', 'Transferencia'),
        ('ajuste', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    cantidad_anterior = models.IntegerField()
    cantidad_nueva = models.IntegerField()
    
    # Para transferencias
    sucursal_destino = models.ForeignKey(
        Sucursal, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='movimientos_recibidos'
    )
    
    # Información del lote (si aplica)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Información adicional
    motivo = models.CharField(max_length=200, blank=True)
    numero_documento = models.CharField(max_length=50, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} ({self.fecha.strftime('%d/%m/%Y')})"

class HistorialPrecios(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    # ✅ PROVEEDOR AHORA OPCIONAL - para precios directos del producto
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Proveedor (opcional - solo para precios de compra)"
    )
    
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    # ✅ NUEVO CAMPO - precio anterior para ver variaciones
    precio_anterior = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio anterior (para calcular variaciones)"
    )
    
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # ✅ NUEVO CAMPO - tipo de precio
    tipo_precio = models.CharField(
        max_length=20,
        choices=[
            ('producto', 'Precio del Producto'),
            ('proveedor', 'Precio de Proveedor'),
            ('lote', 'Precio de Lote'),
        ],
        default='proveedor'
    )
    
    # ✅ NUEVO CAMPO - motivo del cambio
    motivo = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('manual', 'Actualización manual'),
            ('lote', 'Precio desde lote'),
            ('proveedor', 'Actualización de proveedor'),
            ('descuento', 'Aplicación de descuento'),
            ('aumento', 'Aumento de precio'),
            ('correccion', 'Corrección de precio'),
            ('inicial', 'Precio inicial'),
        ],
        default='manual'
    )
    
    # ✅ NUEVO CAMPO - observaciones
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones sobre el cambio de precio"
    )

    class Meta:
        verbose_name_plural = "Historial de Precios"
        ordering = ['-fecha']

    def __str__(self):
        if self.proveedor:
            return f"{self.producto.nombre} - {self.proveedor.nombre} (${self.precio})"
        else:
            return f"{self.producto.nombre} - Precio Producto (${self.precio})"
    
    # ✅ NUEVOS MÉTODOS
    @property
    def variacion_porcentual(self):
        """Calcula la variación porcentual del precio"""
        if self.precio_anterior and self.precio_anterior > 0:
            variacion = ((self.precio - self.precio_anterior) / self.precio_anterior) * 100
            return round(variacion, 2)
        return None
    
    @property
    def tipo_cambio(self):
        """Determina si es aumento, disminución o precio inicial"""
        if not self.precio_anterior:
            return 'inicial'
        elif self.precio > self.precio_anterior:
            return 'aumento'
        elif self.precio < self.precio_anterior:
            return 'disminucion'
        else:
            return 'sin_cambio'
    
    @property
    def es_precio_producto(self):
        """Verifica si es un precio directo del producto"""
        return self.tipo_precio == 'producto'
    
    @property
    def es_precio_proveedor(self):
        """Verifica si es un precio de proveedor"""
        return self.tipo_precio == 'proveedor'

def crear_historial_precio_producto(producto, precio_nuevo, usuario=None, observaciones=''):
    """
    Crea un registro en el historial usando el modelo existente
    Para precios directos del producto (sin proveedor)
    """
    from .models import HistorialPrecios
    from django.utils import timezone
    
    precio_anterior = producto.precio
    
    print(f"💰 Creando historial - Precio anterior: {precio_anterior}, Precio nuevo: {precio_nuevo}")
    
    # Solo crear historial si el precio realmente cambió o es la primera vez
    if precio_anterior != precio_nuevo:
        try:
            historial = HistorialPrecios.objects.create(
                producto=producto,
                proveedor=None,  # Sin proveedor para precios directos
                precio=precio_nuevo,
                usuario=usuario,
                fecha=timezone.now()
            )
            print(f"✅ Historial creado exitosamente: ID {historial.id}")
            return historial
        except Exception as e:
            print(f"❌ Error al crear historial: {e}")
            return None
    else:
        print("ℹ️ Precio sin cambios, no se crea historial")
        return None

class AlertaStock(models.Model):
    TIPO_CHOICES = [
        ('stock_bajo', 'Stock Bajo'),
        ('vencimiento', 'Próximo Vencimiento'),
        ('vencido', 'Producto Vencido'),
    ]
    
    STATUS_CHOICES = [
        ('activa', 'Activa'),
        ('resuelta', 'Resuelta'),
        ('descartada', 'Descartada'),
    ]
    
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, null=True, blank=True)
    mensaje = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='activa')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    usuario_resolucion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Alertas de Stock"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre}"
    
# inventario/models.py - Agregar al final del archivo

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    """
    Extensión del modelo User para roles específicos del sistema
    """
    ROLES = [
        ('administrador', 'Administrador'),
        ('gestor_inventario', 'Gestor de Inventario'),
        ('usuario_lectura', 'Usuario (Solo Lectura)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario_lectura')
    sucursal_asignada = models.ForeignKey(
        Sucursal, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Sucursal principal asignada al usuario"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuarios_creados'
    )
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"
    
    def puede_gestionar_productos(self):
        """Puede crear, editar, eliminar productos"""
        return self.rol in ['administrador', 'gestor_inventario']
    
    def puede_gestionar_inventario(self):
        """Puede hacer movimientos de inventario"""
        return self.rol in ['administrador', 'gestor_inventario']
    
    def puede_asignar_ubicaciones(self):
        """Puede asignar productos a ubicaciones"""
        return self.rol in ['administrador', 'gestor_inventario']
    
    def puede_crear_usuarios(self):
        """Solo administradores pueden crear usuarios"""
        return self.rol == 'administrador'
    
    def puede_ver_alertas(self):
        """Puede ver y gestionar alertas"""
        return self.rol in ['administrador', 'gestor_inventario']
    
    def puede_descargar_reportes(self):
        """Puede descargar reportes Excel"""
        return True  # Todos los roles pueden descargar
    
    def solo_lectura(self):
        """Usuario de solo lectura"""
        return self.rol == 'usuario_lectura'

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda el usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


# Función para crear grupos y permisos iniciales
def crear_grupos_y_permisos():
    """
    Crear grupos y permisos iniciales del sistema
    Ejecutar en: python manage.py shell
    >>> from inventario.models import crear_grupos_y_permisos
    >>> crear_grupos_y_permisos()
    """
    
    # Crear grupos
    admin_group, created = Group.objects.get_or_create(name='Administradores')
    gestor_group, created = Group.objects.get_or_create(name='Gestores de Inventario')
    usuario_group, created = Group.objects.get_or_create(name='Usuarios de Lectura')
    
    # Obtener content types
    from django.contrib.contenttypes.models import ContentType
    
    # Permisos para modelos del inventario
    content_types = [
        ContentType.objects.get_for_model(Producto),
        ContentType.objects.get_for_model(Inventario),
        ContentType.objects.get_for_model(MovimientoInventario),
        ContentType.objects.get_for_model(Ubicacion),
        ContentType.objects.get_for_model(AlertaStock),
        ContentType.objects.get_for_model(Lote),
        ContentType.objects.get_for_model(Sucursal),
        ContentType.objects.get_for_model(Proveedor),
        ContentType.objects.get_for_model(Categoria),
    ]
    
    # Permisos para Administradores (todos)
    for ct in content_types:
        permisos = Permission.objects.filter(content_type=ct)
        admin_group.permissions.add(*permisos)
    
    # Permisos adicionales para admin
    user_ct = ContentType.objects.get_for_model(User)
    perfil_ct = ContentType.objects.get_for_model(PerfilUsuario)
    admin_permisos_user = Permission.objects.filter(content_type__in=[user_ct, perfil_ct])
    admin_group.permissions.add(*admin_permisos_user)
    
    # Permisos para Gestores de Inventario
    gestor_permisos = []
    for ct in content_types:
        if ct.model in ['user', 'perfilusuario']:
            continue  # No pueden gestionar usuarios
        
        # Pueden ver todo, crear/editar/eliminar productos y hacer movimientos
        permisos = Permission.objects.filter(
            content_type=ct,
            codename__in=[
                f'view_{ct.model}',
                f'add_{ct.model}',
                f'change_{ct.model}',
                f'delete_{ct.model}' if ct.model in ['producto', 'movimientoinventario', 'lote'] else None
            ]
        ).exclude(codename__isnull=True)
        gestor_permisos.extend(permisos)
    
    gestor_group.permissions.add(*gestor_permisos)
    
    # Permisos para Usuarios de Lectura (solo view)
    usuario_permisos = []
    for ct in content_types:
        if ct.model in ['user', 'perfilusuario']:
            continue
        
        view_perm = Permission.objects.filter(
            content_type=ct,
            codename=f'view_{ct.model}'
        )
        usuario_permisos.extend(view_perm)
    
    usuario_group.permissions.add(*usuario_permisos)
    
    print("✅ Grupos y permisos creados exitosamente:")
    print(f"- Administradores: {admin_group.permissions.count()} permisos")
    print(f"- Gestores de Inventario: {gestor_group.permissions.count()} permisos")
    print(f"- Usuarios de Lectura: {usuario_group.permissions.count()} permisos")    

