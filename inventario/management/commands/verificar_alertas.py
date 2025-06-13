from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventario.models import *
from django.db import models

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