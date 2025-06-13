from django.urls import path
from . import views
from django.shortcuts import redirect

def admin_login_redirect(request):
    return redirect('login')

urlpatterns = [
    path('admin/login/', admin_login_redirect, name='admin_login_override'),
    # ==================
    # AUTENTICACIÓN
    # ==================

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # ==================
    # GESTIÓN DE USUARIOS (Solo Administradores)
    # ==================
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:user_id>/', views.detalle_usuario, name='detalle_usuario'),
    path('usuarios/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:user_id>/toggle-activo/', views.toggle_usuario_activo, name='toggle_usuario_activo'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),


    # ==================
    # PERFIL PERSONAL
    # ==================
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # Productos (Gestores e Administradores)
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:producto_id>/precio/',  views.actualizar_precio_producto, name='actualizar_precio_producto'),
    path('productos/<int:producto_id>/precio/ajax/', views.actualizar_precio_ajax, name='actualizar_precio_ajax'),
    
    
    # Movimientos (Gestores e Administradores)
    path('productos/<int:producto_id>/movimiento/', views.movimiento_inventario, name='movimiento_inventario'),
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    
    # Alertas (Gestores e Administradores)
    path('alertas/', views.alertas_stock, name='alertas_stock'),
    path('alertas/<int:alerta_id>/resolver/', views.resolver_alerta, name='resolver_alerta'),
    
    # Proveedores (Gestores e Administradores)
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/<int:proveedor_id>/editar/', views.editar_proveedor, name='editar_proveedor'),
    
    # Lotes (Gestores e Administradores)
    path('productos/<int:producto_id>/lotes/', views.lista_lotes, name='lista_lotes'),
    path('productos/<int:producto_id>/lotes/crear/', views.crear_lote, name='crear_lote'),
    path('lotes/<int:lote_id>/editar/', views.editar_lote, name='editar_lote'),
    path('lotes/<int:lote_id>/', views.detalle_lote, name='detalle_lote'),
    
    # Categorías y Etiquetas
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('etiquetas/', views.lista_etiquetas, name='lista_etiquetas'),
    path('etiquetas/crear/', views.crear_etiqueta, name='crear_etiqueta'),
    
    # Sucursales (Solo Administradores)
    path('sucursales/', views.lista_sucursales, name='lista_sucursales'),
    path('sucursales/crear/', views.crear_sucursal, name='crear_sucursal'),
    path('sucursales/<int:sucursal_id>/editar/', views.editar_sucursal, name='editar_sucursal'),
    
    # Reportes (Todos los roles)
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/generar/', views.generar_reporte, name='generar_reporte'),
    
    # API endpoints para AJAX
    path('api/producto-stock/<int:producto_id>/', views.api_producto_stock, name='api_producto_stock'),
    path('api/buscar-productos/', views.api_buscar_productos, name='api_buscar_productos'),
    path('api/cambiar-sucursal/', views.cambiar_sucursal, name='cambiar_sucursal'),
    path('api/alertas-count/', views.api_alertas_count, name='api_alertas_count'),

    path('productos/<int:producto_id>/movimiento/', views.movimiento_inventario, name='movimiento_inventario'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('alertas/<int:alerta_id>/resolver/', views.resolver_alerta, name='resolver_alerta'),
    path('proveedores/<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),

    # Etiquetas
    path('etiquetas/', views.lista_etiquetas, name='lista_etiquetas'),
    path('etiquetas/crear/', views.crear_etiqueta, name='crear_etiqueta'),
    path('etiquetas/<int:etiqueta_id>/editar/', views.editar_etiqueta, name='editar_etiqueta'),

    # URLs de Ubicaciones (Gestores e Administradores)
    path('sucursales/<int:sucursal_id>/ubicaciones/', views.lista_ubicaciones, name='lista_ubicaciones'),
    path('sucursales/<int:sucursal_id>/ubicaciones/crear/', views.crear_ubicacion, name='crear_ubicacion'),
    path('sucursales/<int:sucursal_id>/ubicaciones/mapa/', views.mapa_ubicaciones, name='mapa_ubicaciones'),
    path('sucursales/<int:sucursal_id>/ubicaciones/<int:ubicacion_id>/', views.detalle_ubicacion, name='detalle_ubicacion'),
    path('sucursales/<int:sucursal_id>/ubicaciones/<int:ubicacion_id>/editar/', views.editar_ubicacion, name='editar_ubicacion'),
    path('sucursales/<int:sucursal_id>/ubicaciones/<int:ubicacion_id>/asignar/', views.asignar_ubicacion, name='asignar_ubicacion'),
    path('inventario/<int:inventario_id>/asignar-ubicacion/', views.asignar_ubicacion_producto, name='asignar_ubicacion_producto'),
    path('sucursales/<int:sucursal_id>/ubicaciones/<int:ubicacion_id>/eliminar/', views.eliminar_ubicacion, name='eliminar_ubicacion'),

    # Comentarios para implementación:
    # 
    # VISTAS QUE NECESITAN DECORADORES DE PERMISOS:
    # 
    # @gestor_o_admin:
    # - crear_producto, editar_producto, eliminar_producto
    # - crear_ubicacion, editar_ubicacion, eliminar_ubicacion, asignar_ubicacion
    # - crear_movimiento
    # - lista_alertas, resolver_alerta, descartar_alerta
    # - crear_proveedor, editar_proveedor
    # - crear_lote, editar_lote
    # 
    # @solo_administrador:
    # - crear_sucursal, editar_sucursal
    # - crear_categoria, editar_categoria
    # - lista_usuarios, crear_usuario, editar_usuario, etc.
    # 
    # @todos_los_roles:
    # - lista_productos, detalle_producto
    # - lista_ubicaciones, detalle_ubicacion, mapa_ubicaciones
    # - lista_movimientos, detalle_movimiento
    # - lista_proveedores, detalle_proveedor
    # - lista_lotes, detalle_lote
    # - todos los reportes
    # - dashboard
    # - mi_perfil


]