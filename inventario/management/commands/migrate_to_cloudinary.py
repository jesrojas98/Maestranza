from django.core.management.base import BaseCommand
from django.core.files import File
import os
import cloudinary.uploader
from tu_app.models import Producto  # Cambia por tu app

class Command(BaseCommand):
    help = 'Migra imágenes existentes a Cloudinary'

    def handle(self, *args, **options):
        productos_con_imagen = Producto.objects.exclude(imagen='').exclude(imagen__isnull=True)
        total = productos_con_imagen.count()
        
        self.stdout.write(f'Encontrados {total} productos con imágenes para migrar...')
        
        migrados = 0
        errores = 0
        
        for i, producto in enumerate(productos_con_imagen, 1):
            try:
                # Verificar si la imagen existe físicamente
                if hasattr(producto.imagen, 'path') and os.path.exists(producto.imagen.path):
                    self.stdout.write(f'[{i}/{total}] Migrando {producto.nombre}...')
                    
                    # Subir a Cloudinary manualmente
                    result = cloudinary.uploader.upload(
                        producto.imagen.path,
                        folder='productos',
                        public_id=f'producto_{producto.id}_{producto.codigo}',
                        transformation=[
                            {'quality': 'auto:good'},
                            {'fetch_format': 'auto'},
                            {'width': 800, 'height': 600, 'crop': 'limit'}
                        ]
                    )
                    
                    # Actualizar el campo con la nueva URL
                    producto.imagen = result['public_id']
                    producto.save(update_fields=['imagen'])
                    
                    migrados += 1
                    self.stdout.write(f'  ✅ Migrado: {result["secure_url"]}')
                else:
                    self.stdout.write(f'  ⚠️  Archivo no encontrado: {producto.imagen}')
                    errores += 1
                    
            except Exception as e:
                self.stdout.write(f'  ❌ Error: {str(e)}')
                errores += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Migración completada: {migrados} exitosos, {errores} errores'
            )
        )

# ===================================================================
# utils/cloudinary_helpers.py - Funciones útiles

import cloudinary
import cloudinary.uploader
from django.conf import settings

def upload_image_to_cloudinary(image_file, folder='productos', public_id=None):
    """
    Sube una imagen a Cloudinary con configuraciones optimizadas
    """
    try:
        options = {
            'folder': folder,
            'resource_type': 'image',
            'transformation': [
                {'quality': 'auto:good'},
                {'fetch_format': 'auto'},
                {'width': 800, 'height': 600, 'crop': 'limit'}
            ]
        }
        
        if public_id:
            options['public_id'] = public_id
            
        result = cloudinary.uploader.upload(image_file, **options)
        return result
        
    except Exception as e:
        print(f"Error subiendo imagen a Cloudinary: {e}")
        return None

def delete_cloudinary_image(public_id):
    """
    Elimina una imagen de Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error eliminando imagen de Cloudinary: {e}")
        return False

def get_optimized_url(public_id, width=None, height=None, crop='limit', quality='auto:good'):
    """
    Genera URL optimizada para una imagen en Cloudinary
    """
    try:
        from cloudinary import CloudinaryImage
        
        transformations = {'quality': quality, 'fetch_format': 'auto'}
        if width:
            transformations['width'] = width
        if height:
            transformations['height'] = height
        if width or height:
            transformations['crop'] = crop
            
        return CloudinaryImage(public_id).build_url(**transformations)
        
    except Exception as e:
        print(f"Error generando URL optimizada: {e}")
        return None

# ===================================================================
# signals.py - Limpieza automática de imágenes

from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import Producto
import cloudinary.uploader

@receiver(pre_delete, sender=Producto)
def delete_producto_image_on_delete(sender, instance, **kwargs):
    """
    Elimina la imagen de Cloudinary cuando se borra el producto
    """
    if instance.imagen:
        try:
            # Extraer public_id de la imagen
            public_id = instance.imagen.public_id
            cloudinary.uploader.destroy(public_id)
            print(f"Imagen eliminada de Cloudinary: {public_id}")
        except Exception as e:
            print(f"Error eliminando imagen de Cloudinary: {e}")

@receiver(pre_save, sender=Producto)
def delete_old_image_on_update(sender, instance, **kwargs):
    """
    Elimina la imagen anterior de Cloudinary cuando se actualiza
    """
    if instance.pk:
        try:
            old_instance = Producto.objects.get(pk=instance.pk)
            if old_instance.imagen and old_instance.imagen != instance.imagen:
                public_id = old_instance.imagen.public_id
                cloudinary.uploader.destroy(public_id)
                print(f"Imagen anterior eliminada de Cloudinary: {public_id}")
        except Producto.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error eliminando imagen anterior: {e}")