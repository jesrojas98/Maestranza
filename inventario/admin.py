# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'activa', 'created_at']
    list_filter = ['activa', 'created_at']
    search_fields = ['nombre', 'direccion']
    list_editable = ['activa']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'contacto', 'telefono', 'email', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'contacto', 'email']
    list_editable = ['activo']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'mostrar_color']
    search_fields = ['nombre']
    
    def mostrar_color(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    mostrar_color.short_description = 'Color'

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'mostrar_color']
    search_fields = ['nombre']
    
    def mostrar_color(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.color, obj.nombre
        )
    mostrar_color.short_description = 'Vista previa'

class InventarioInline(admin.TabularInline):
    model = Inventario
    extra = 0
    readonly_fields = ['updated_at']

class LoteInline(admin.TabularInline):
    model = Lote
    extra = 0
    readonly_fields = ['fecha_compra']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre', 'categoria', 'stock_minimo', 
        'maneja_lotes', 'maneja_vencimiento', 'activo', 'created_at'
    ]
    list_filter = [
        'categoria', 'maneja_lotes', 'maneja_vencimiento', 
        'activo', 'created_at'
    ]
    search_fields = ['codigo', 'nombre', 'descripcion']
    list_editable = ['activo']
    filter_horizontal = ['etiquetas']
    inlines = [InventarioInline, LoteInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Clasificación', {
            'fields': ('etiquetas',)
        }),
        ('Configuración de Stock', {
            'fields': ('unidad_medida', 'stock_minimo', 'maneja_lotes', 'maneja_vencimiento')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = [
        'producto', 'sucursal', 'cantidad', 'ubicacion', 
        'necesita_reposicion_display', 'updated_at'
    ]
    list_filter = ['sucursal', 'updated_at']
    search_fields = ['producto__nombre', 'producto__codigo', 'ubicacion']
    list_select_related = ['producto', 'sucursal']
    
    def necesita_reposicion_display(self, obj):
        if obj.necesita_reposicion:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Sí</span>'
            )
        return format_html('<span style="color: green;">✅ No</span>')
    necesita_reposicion_display.short_description = 'Necesita Reposición'

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'producto', 'proveedor', 'fecha_vencimiento', 
        'estado_vencimiento', 'precio_compra', 'fecha_compra'
    ]
    list_filter = ['proveedor', 'fecha_vencimiento', 'fecha_compra']
    search_fields = ['codigo', 'producto__nombre', 'producto__codigo']
    list_select_related = ['producto', 'proveedor']
    date_hierarchy = 'fecha_vencimiento'
    
    def estado_vencimiento(self, obj):
        if obj.esta_vencido:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Vencido</span>')
        elif obj.dias_vencimiento and obj.dias_vencimiento <= 30:
            return format_html('<span style="color: orange; font-weight: bold;">🟡 Por vencer</span>')
        else:
            return format_html('<span style="color: green;">🟢 Vigente</span>')
    estado_vencimiento.short_description = 'Estado'

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'producto', 'sucursal', 'tipo', 'cantidad', 
        'cantidad_anterior', 'cantidad_nueva', 'usuario'
    ]
    list_filter = ['tipo', 'sucursal', 'fecha']
    search_fields = ['producto__nombre', 'producto__codigo', 'motivo']
    list_select_related = ['producto', 'sucursal', 'usuario']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('producto', 'sucursal', 'tipo', 'cantidad')
        }),
        ('Transferencia (si aplica)', {
            'fields': ('sucursal_destino',)
        }),
        ('Información del Lote', {
            'fields': ('lote',)
        }),
        ('Detalles Adicionales', {
            'fields': ('motivo', 'numero_documento')
        }),
        ('Información del Sistema', {
            'fields': ('cantidad_anterior', 'cantidad_nueva', 'usuario', 'fecha'),
            'classes': ('collapse',)
        }),
    )

@admin.register(HistorialPrecios)
class HistorialPreciosAdmin(admin.ModelAdmin):
    list_display = ['producto', 'proveedor', 'precio', 'fecha', 'usuario']
    list_filter = ['proveedor', 'fecha']
    search_fields = ['producto__nombre', 'producto__codigo', 'proveedor__nombre']
    list_select_related = ['producto', 'proveedor', 'usuario']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha']

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = [
        'tipo', 'producto', 'sucursal', 'status', 
        'fecha_creacion', 'usuario_resolucion'
    ]
    list_filter = ['tipo', 'status', 'sucursal', 'fecha_creacion']
    search_fields = ['producto__nombre', 'producto__codigo', 'mensaje']
    list_select_related = ['producto', 'sucursal', 'usuario_resolucion']
    list_editable = ['status']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('tipo', 'producto', 'sucursal', 'lote', 'mensaje')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Resolución', {
            'fields': ('fecha_resolucion', 'usuario_resolucion'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_como_resueltas', 'marcar_como_activas']
    
    def marcar_como_resueltas(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='resuelta',
            fecha_resolucion=timezone.now(),
            usuario_resolucion=request.user
        )
        self.message_user(request, f'{updated} alertas marcadas como resueltas.')
    marcar_como_resueltas.short_description = 'Marcar alertas seleccionadas como resueltas'
    
    def marcar_como_activas(self, request, queryset):
        updated = queryset.update(
            status='activa',
            fecha_resolucion=None,
            usuario_resolucion=None
        )
        self.message_user(request, f'{updated} alertas marcadas como activas.')
    marcar_como_activas.short_description = 'Marcar alertas seleccionadas como activas'

# Configuración del sitio de administración
admin.site.site_header = 'Administración - Sistema de Inventario Ferretería'
admin.site.site_title = 'Inventario Ferretería'
admin.site.index_title = 'Panel de Administración'