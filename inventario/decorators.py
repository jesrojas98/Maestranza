from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def rol_requerido(*roles_permitidos):
    """
    Decorador para verificar que el usuario tenga uno de los roles especificados
    
    Uso:
    @rol_requerido('administrador', 'gestor_inventario')
    def mi_vista(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'perfil'):
                messages.error(request, 'Su cuenta no tiene un perfil asignado. Contacte al administrador.')
                return redirect('dashboard')
            
            if not request.user.perfil.activo:
                messages.error(request, 'Su cuenta está inactiva. Contacte al administrador.')
                return redirect('dashboard')
            
            if request.user.perfil.rol not in roles_permitidos:
                messages.error(request, 'No tiene permisos para acceder a esta funcionalidad.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def solo_administrador(view_func):
    """Decorador para vistas que solo pueden acceder administradores"""
    return rol_requerido('administrador')(view_func)

def gestor_o_admin(view_func):
    """Decorador para vistas que pueden acceder gestores e administradores"""
    return rol_requerido('administrador', 'gestor_inventario')(view_func)

def todos_los_roles(view_func):
    """Decorador para vistas que pueden acceder todos los roles autenticados"""
    return rol_requerido('administrador', 'gestor_inventario', 'usuario_lectura')(view_func)

def puede_gestionar_productos(view_func):
    """Decorador específico para gestión de productos"""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or not request.user.perfil.puede_gestionar_productos():
            messages.error(request, 'No tiene permisos para gestionar productos.')
            return redirect('lista_productos')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def puede_gestionar_inventario(view_func):
    """Decorador específico para movimientos de inventario"""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or not request.user.perfil.puede_gestionar_inventario():
            messages.error(request, 'No tiene permisos para gestionar inventario.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def puede_asignar_ubicaciones(view_func):
    """Decorador específico para asignación de ubicaciones"""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or not request.user.perfil.puede_asignar_ubicaciones():
            messages.error(request, 'No tiene permisos para asignar ubicaciones.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def puede_ver_alertas(view_func):
    """Decorador específico para ver alertas"""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or not request.user.perfil.puede_ver_alertas():
            messages.error(request, 'No tiene permisos para ver alertas.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped_view

def verificar_permiso_ajax(rol_requerido):
    """
    Decorador para vistas AJAX que requieren verificación de permisos
    Retorna JSON con error en lugar de redireccionar
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            from django.http import JsonResponse
            
            if not hasattr(request.user, 'perfil'):
                return JsonResponse({
                    'success': False, 
                    'error': 'Su cuenta no tiene un perfil asignado.'
                }, status=403)
            
            if not request.user.perfil.activo:
                return JsonResponse({
                    'success': False, 
                    'error': 'Su cuenta está inactiva.'
                }, status=403)
            
            if request.user.perfil.rol not in rol_requerido:
                return JsonResponse({
                    'success': False, 
                    'error': 'No tiene permisos para realizar esta acción.'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

# Función helper para templates
def obtener_permisos_usuario(user):
    """
    Función helper para usar en templates y obtener permisos del usuario
    """
    if not hasattr(user, 'perfil'):
        return {
            'puede_gestionar_productos': False,
            'puede_gestionar_inventario': False,
            'puede_asignar_ubicaciones': False,
            'puede_crear_usuarios': False,
            'puede_ver_alertas': False,
            'puede_descargar_reportes': False,
            'solo_lectura': True,
            'rol': 'sin_perfil'
        }
    
    perfil = user.perfil
    return {
        'puede_gestionar_productos': perfil.puede_gestionar_productos(),
        'puede_gestionar_inventario': perfil.puede_gestionar_inventario(),
        'puede_asignar_ubicaciones': perfil.puede_asignar_ubicaciones(),
        'puede_crear_usuarios': perfil.puede_crear_usuarios(),
        'puede_ver_alertas': perfil.puede_ver_alertas(),
        'puede_descargar_reportes': perfil.puede_descargar_reportes(),
        'solo_lectura': perfil.solo_lectura(),
        'rol': perfil.get_rol_display(),
        'rol_codigo': perfil.rol
    }