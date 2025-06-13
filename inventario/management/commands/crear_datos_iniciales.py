from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventario.models import *

class Command(BaseCommand):
    help = 'Crea datos iniciales para el sistema de inventario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Crear datos de demostración adicionales',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales...')
        
        # Crear categorías
        categorias_data = [
            {'nombre': 'Herramientas Manuales', 'descripcion': 'Martillos, destornilladores, llaves', 'color': '#007bff'},
            {'nombre': 'Herramientas Eléctricas', 'descripcion': 'Taladros, sierras, amoladoras', 'color': '#28a745'},
            {'nombre': 'Materiales de Construcción', 'descripcion': 'Cemento, ladrillos, arena', 'color': '#ffc107'},
            {'nombre': 'Plomería', 'descripcion': 'Tubos, llaves, accesorios', 'color': '#17a2b8'},
            {'nombre': 'Electricidad', 'descripcion': 'Cables, enchufes, interruptores', 'color': '#dc3545'},
            {'nombre': 'Pintura', 'descripcion': 'Pinturas, brochas, rodillos', 'color': '#6f42c1'},
            {'nombre': 'Ferretería General', 'descripcion': 'Tornillos, clavos, tuercas', 'color': '#fd7e14'},
        ]
        
        for cat_data in categorias_data:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✓ Categoría creada: {categoria.nombre}')
        
        # Crear etiquetas
        etiquetas_data = [
            {'nombre': 'Nuevo', 'color': '#28a745'},
            {'nombre': 'Oferta', 'color': '#dc3545'},
            {'nombre': 'Importado', 'color': '#007bff'},
            {'nombre': 'Nacional', 'color': '#28a745'},
            {'nombre': 'Promoción', 'color': '#ffc107'},
            {'nombre': 'Liquidación', 'color': '#6c757d'},
        ]
        
        for etiq_data in etiquetas_data:
            etiqueta, created = Etiqueta.objects.get_or_create(
                nombre=etiq_data['nombre'],
                defaults=etiq_data
            )
            if created:
                self.stdout.write(f'✓ Etiqueta creada: {etiqueta.nombre}')
        
        # Crear sucursales
        sucursales_data = [
            {
                'nombre': 'Sucursal Centro',
                'direccion': 'Av. Principal 123, Centro, Santiago',
                'telefono': '+56 2 2234 5678'
            },
            {
                'nombre': 'Sucursal Norte',
                'direccion': 'Av. Los Libertadores 456, Las Condes, Santiago',
                'telefono': '+56 2 2345 6789'
            },
            {
                'nombre': 'Sucursal Sur',
                'direccion': 'Av. Vicuña Mackenna 789, La Florida, Santiago',
                'telefono': '+56 2 2456 7890'
            },
        ]
        
        for suc_data in sucursales_data:
            sucursal, created = Sucursal.objects.get_or_create(
                nombre=suc_data['nombre'],
                defaults=suc_data
            )
            if created:
                self.stdout.write(f'✓ Sucursal creada: {sucursal.nombre}')
        
        # Crear proveedores
        proveedores_data = [
            {
                'nombre': 'Ferretería Mayorista S.A.',
                'contacto': 'Juan Pérez',
                'telefono': '+56 2 2111 2222',
                'email': 'ventas@ferremayorista.cl',
                'direccion': 'Av. Industrial 100, Quilicura'
            },
            {
                'nombre': 'Herramientas Pro Ltda.',
                'contacto': 'María González',
                'telefono': '+56 2 2333 4444',
                'email': 'contacto@herramientaspro.cl',
                'direccion': 'San Pablo 200, Santiago Centro'
            },
            {
                'nombre': 'Distribuidora El Martillo',
                'contacto': 'Carlos Silva',
                'telefono': '+56 2 2555 6666',
                'email': 'carlos@elmartillo.cl',
                'direccion': 'Av. Dorsal 300, Maipú'
            },
        ]
        
        for prov_data in proveedores_data:
            proveedor, created = Proveedor.objects.get_or_create(
                nombre=prov_data['nombre'],
                defaults=prov_data
            )
            if created:
                self.stdout.write(f'✓ Proveedor creado: {proveedor.nombre}')
        
        if options['demo']:
            self.crear_datos_demo()
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos iniciales creados exitosamente!')
        )
    
    def crear_datos_demo(self):
        """Crear productos de demostración"""
        self.stdout.write('Creando productos de demostración...')
        
        # Obtener categorías y proveedores
        cat_herramientas = Categoria.objects.get(nombre='Herramientas Manuales')
        cat_electricas = Categoria.objects.get(nombre='Herramientas Eléctricas')
        cat_plomeria = Categoria.objects.get(nombre='Plomería')
        
        proveedor1 = Proveedor.objects.first()
        proveedor2 = Proveedor.objects.last()
        
        etiqueta_nuevo = Etiqueta.objects.get(nombre='Nuevo')
        etiqueta_oferta = Etiqueta.objects.get(nombre='Oferta')
        
        # Productos de demostración
        productos_demo = [
            {
                'codigo': 'MART001',
                'nombre': 'Martillo de Carpintero 16oz',
                'descripcion': 'Martillo profesional con mango de fibra de vidrio',
                'categoria': cat_herramientas,
                'stock_minimo': 10,
                'unidad_medida': 'unidad'
            },
            {
                'codigo': 'TALAD001',
                'nombre': 'Taladro Percutor 13mm 600W',
                'descripcion': 'Taladro eléctrico con percutor, incluye maletín',
                'categoria': cat_electricas,
                'stock_minimo': 5,
                'unidad_medida': 'unidad'
            },
            {
                'codigo': 'TUBE001',
                'nombre': 'Tubo PVC 110mm x 3m',
                'descripcion': 'Tubo PVC para desagüe, color gris',
                'categoria': cat_plomeria,
                'stock_minimo': 20,
                'unidad_medida': 'metro'
            },
            {
                'codigo': 'DEST001',
                'nombre': 'Set Destornilladores 6 piezas',
                'descripcion': 'Set de destornilladores planos y Phillips',
                'categoria': cat_herramientas,
                'stock_minimo': 8,
                'unidad_medida': 'set'
            },
        ]
        
        sucursales = Sucursal.objects.all()
        
        for prod_data in productos_demo:
            producto, created = Producto.objects.get_or_create(
                codigo=prod_data['codigo'],
                defaults=prod_data
            )
            
            if created:
                # Agregar etiquetas
                producto.etiquetas.add(etiqueta_nuevo)
                if 'Set' in producto.nombre:
                    producto.etiquetas.add(etiqueta_oferta)
                
                # Crear inventario inicial en todas las sucursales
                for sucursal in sucursales:
                    stock_inicial = 15 if sucursal.nombre == 'Sucursal Centro' else 10
                    Inventario.objects.create(
                        producto=producto,
                        sucursal=sucursal,
                        cantidad=stock_inicial,
                        ubicacion=f'Pasillo A-{producto.categoria.nombre[:1]}'
                    )
                
                # Crear lote si es apropiado
                if producto.codigo in ['MART001', 'TALAD001']:
                    Lote.objects.create(
                        codigo=f'L{producto.codigo}001',
                        producto=producto,
                        proveedor=proveedor1,
                        precio_compra=15000 if 'Martillo' in producto.nombre else 45000
                    )
                
                # Crear historial de precios
                HistorialPrecios.objects.create(
                    producto=producto,
                    proveedor=proveedor1,
                    precio=15000 if 'Martillo' in producto.nombre else 45000
                )
                
                self.stdout.write(f'✓ Producto demo creado: {producto.nombre}')
        
        # Crear algunos movimientos de demostración
        productos = Producto.objects.all()[:2]
        sucursal_centro = Sucursal.objects.get(nombre='Sucursal Centro')
        user = User.objects.first()
        
        for producto in productos:
            inventario = Inventario.objects.get(producto=producto, sucursal=sucursal_centro)
            
            # Movimiento de entrada
            MovimientoInventario.objects.create(
                producto=producto,
                sucursal=sucursal_centro,
                tipo='entrada',
                cantidad=20,
                cantidad_anterior=inventario.cantidad - 20,
                cantidad_nueva=inventario.cantidad,
                motivo='Compra inicial',
                numero_documento='FC-001',
                usuario=user
            )
        
        self.stdout.write('✓ Datos de demostración creados')

# inventario/management/commands/verificar_alertas.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventario.models import *

class Command(BaseCommand):
    help = 'Verifica y crea alertas de stock bajo y vencimientos'

    def handle(self, *args, **options):
        self.stdout.write('Verificando alertas...')
        
        alertas_creadas = 0
        
        # Verificar stock bajo
        inventarios_bajo = Inventario.objects.filter(
            cantidad__lte=models.F('producto__stock_minimo'),
            producto__activo=True
        )
        
        for inventario in inventarios_bajo:
            alerta, created = AlertaStock.objects.get_or_create(
                tipo='stock_bajo',
                producto=inventario.producto,
                sucursal=inventario.sucursal,
                status='activa',
                defaults={
                    'mensaje': f'Stock bajo para {inventario.producto.nombre} en {inventario.sucursal.nombre}. '
                             f'Stock actual: {inventario.cantidad}, Mínimo: {inventario.producto.stock_minimo}'
                }
            )
            if created:
                alertas_creadas += 1
                self.stdout.write(f'✓ Alerta de stock bajo: {inventario.producto.nombre}')
        
        # Verificar productos próximos a vencer (30 días)
        fecha_limite = timezone.now().date() + timedelta(days=30)
        lotes_vencer = Lote.objects.filter(
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gt=timezone.now().date()
        )
        
        for lote in lotes_vencer:
            # Buscar en qué sucursales hay stock de este lote
            for sucursal in Sucursal.objects.filter(activa=True):
                alerta, created = AlertaStock.objects.get_or_create(
                    tipo='vencimiento',
                    producto=lote.producto,
                    sucursal=sucursal,
                    lote=lote,
                    status='activa',
                    defaults={
                        'mensaje': f'Lote {lote.codigo} de {lote.producto.nombre} vence el {lote.fecha_vencimiento.strftime("%d/%m/%Y")}'
                    }
                )
                if created:
                    alertas_creadas += 1
                    self.stdout.write(f'✓ Alerta de vencimiento: {lote.producto.nombre} - Lote {lote.codigo}')
        
        # Verificar productos vencidos
        lotes_vencidos = Lote.objects.filter(
            fecha_vencimiento__lt=timezone.now().date()
        )
        
        for lote in lotes_vencidos:
            for sucursal in Sucursal.objects.filter(activa=True):
                alerta, created = AlertaStock.objects.get_or_create(
                    tipo='vencido',
                    producto=lote.producto,
                    sucursal=sucursal,
                    lote=lote,
                    status='activa',
                    defaults={
                        'mensaje': f'¡ATENCIÓN! Lote {lote.codigo} de {lote.producto.nombre} está vencido desde {lote.fecha_vencimiento.strftime("%d/%m/%Y")}'
                    }
                )
                if created:
                    alertas_creadas += 1
                    self.stdout.write(f'⚠️ Alerta de producto vencido: {lote.producto.nombre} - Lote {lote.codigo}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Verificación completada. {alertas_creadas} nuevas alertas creadas.')
        )