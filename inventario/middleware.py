import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import PerfilUsuario

# Configurar logger
logger = logging.getLogger('inventario')

class PermisosMiddleware(MiddlewareMixin):
    """
    Middleware para verificar permisos y registrar actividad de usuarios
    """
    
    # URLs que no requieren verificación de permisos
    URLS_PUBLICAS = [
        'login',
        'logout',
        'admin',
    ]
    
    # URLs que requieren permisos específicos
    URLS_PROTEGIDAS = {
        # Solo Administradores
        'crear_usuario': 'administrador',
        'editar_usuario': 'administrador',
        'lista_usuarios': 'administrador',
        'detalle_usuario': 'administrador',
        'toggle_usuario_activo': 'administrador',
        'crear_sucursal': 'administrador',
        'editar_sucursal': 'administrador',
        'crear_categoria': 'administrador',
        'editar_categoria': 'administrador',
        
        # Gestores e Administradores
        'crear_producto': ['administrador', 'gestor_inventario'],
        'editar_producto': ['administrador', 'gestor_inventario'],
        'eliminar_producto': ['administrador', 'gestor_inventario'],
        'crear_ubicacion': ['administrador', 'gestor_inventario'],
        'editar_ubicacion': ['administrador', 'gestor_inventario'],
        'eliminar_ubicacion': ['administrador', 'gestor_inventario'],
        'asignar_ubicacion': ['administrador', 'gestor_inventario'],
        'crear_movimiento': ['administrador', 'gestor_inventario'],
        'lista_alertas': ['administrador', 'gestor_inventario'],
        'resolver_alerta': ['administrador', 'gestor_inventario'],
        'descartar_alerta': ['administrador', 'gestor_inventario'],
        'crear_proveedor': ['administrador', 'gestor_inventario'],
        'editar_proveedor': ['administrador', 'gestor_inventario'],
        'crear_lote': ['administrador', 'gestor_inventario'],
        'editar_lote': ['administrador', 'gestor_inventario'],
    }
    
    # Acciones que se registran en auditoría
    ACCIONES_AUDITORIA = [
        'crear_producto', 'editar_producto', 'eliminar_producto',
        'crear_movimiento', 'resolver_alerta', 'descartar_alerta',
        'crear_usuario', 'editar_usuario', 'toggle_usuario_activo',
        'crear_sucursal', 'editar_sucursal',
        'asignar_ubicacion', 'crear_ubicacion', 'editar_ubicacion',
    ]

    def process_request(self, request):
        """Procesar solicitud antes de que llegue a la vista"""
        
        # Saltar verificación para URLs públicas
        if not request.user.is_authenticated:
            return None
        
        # Verificar si la URL está en las protegidas
        url_name = self.get_url_name(request)
        if not url_name or url_name in self.URLS_PUBLICAS:
            return None
        
        # Verificar si el usuario tiene perfil
        if not hasattr(request.user, 'perfil'):
            messages.error(request, 'Su cuenta no tiene un perfil asignado. Contacte al administrador.')
            logger.warning(f'Usuario sin perfil intentó acceder: {request.user.username} -> {url_name}')
            return redirect('dashboard')
        
        # Verificar si el usuario está activo
        if not request.user.perfil.activo:
            messages.error(request, 'Su cuenta está inactiva. Contacte al administrador.')
            logger.warning(f'Usuario inactivo intentó acceder: {request.user.username} -> {url_name}')
            return redirect('login')
        
        # Verificar permisos específicos
        if url_name in self.URLS_PROTEGIDAS:
            roles_permitidos = self.URLS_PROTEGIDAS[url_name]
            if isinstance(roles_permitidos, str):
                roles_permitidos = [roles_permitidos]
            
            if request.user.perfil.rol not in roles_permitidos:
                mensaje = 'No tiene permisos para acceder a esta funcionalidad.'
                
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': mensaje
                    }, status=403)
                
                messages.error(request, mensaje)
                logger.warning(
                    f'Acceso denegado: {request.user.username} ({request.user.perfil.rol}) -> {url_name}'
                )
                return redirect('dashboard')
        
        return None

    def process_response(self, request, response):
        """Procesar respuesta después de la vista"""
        
        if not request.user.is_authenticated:
            return response
        
        # Registrar actividad para auditoría
        url_name = self.get_url_name(request)
        if url_name in self.ACCIONES_AUDITORIA and request.method in ['POST', 'PUT', 'DELETE']:
            self.registrar_auditoria(request, url_name, response)
        
        return response

    def get_url_name(self, request):
        """Obtener el nombre de la URL de la solicitud"""
        try:
            return request.resolver_match.url_name
        except AttributeError:
            return None

    def registrar_auditoria(self, request, accion, response):
        """Registrar acción en el sistema de auditoría"""
        try:
            # Solo registrar si la acción fue exitosa
            if response.status_code < 400:
                user = request.user
                ip_address = self.get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Obtener datos adicionales según el tipo de acción
                datos_adicionales = self.obtener_datos_accion(request, accion)
                
                logger.info(
                    f'AUDITORIA: {user.username} ({user.perfil.rol}) ejecutó {accion} desde {ip_address}',
                    extra={
                        'user_id': user.id,
                        'username': user.username,
                        'rol': user.perfil.rol,
                        'accion': accion,
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'datos': datos_adicionales,
                        'sucursal_id': request.session.get('sucursal_id'),
                    }
                )
        except Exception as e:
            logger.error(f'Error registrando auditoría: {e}')

    def get_client_ip(self, request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def obtener_datos_accion(self, request, accion):
        """Obtener datos específicos según el tipo de acción"""
        datos = {}
        
        try:
            if request.method == 'POST' and request.content_type == 'application/json':
                # Para peticiones AJAX
                datos['json_data'] = json.loads(request.body.decode('utf-8'))
            elif request.method == 'POST':
                # Para formularios regulares
                datos['form_data'] = {k: v for k, v in request.POST.items() 
                                    if k not in ['csrfmiddlewaretoken', 'password', 'password_confirm']}
            
            # Datos específicos por acción
            if 'producto' in accion:
                producto_id = request.resolver_match.kwargs.get('producto_id')
                if producto_id:
                    datos['producto_id'] = producto_id
            
            elif 'usuario' in accion:
                user_id = request.resolver_match.kwargs.get('user_id')
                if user_id:
                    datos['user_id'] = user_id
            
            elif 'ubicacion' in accion:
                ubicacion_id = request.resolver_match.kwargs.get('ubicacion_id')
                sucursal_id = request.resolver_match.kwargs.get('sucursal_id')
                if ubicacion_id:
                    datos['ubicacion_id'] = ubicacion_id
                if sucursal_id:
                    datos['sucursal_id'] = sucursal_id
            
        except Exception as e:
            logger.error(f'Error obteniendo datos de acción: {e}')
        
        return datos


class SesionSeguridadMiddleware(MiddlewareMixin):
    """
    Middleware para manejar seguridad de sesiones
    """
    
    def process_request(self, request):
        """Verificar seguridad de la sesión"""
        
        if not request.user.is_authenticated:
            return None
        
        try:
            # Verificar si el perfil del usuario sigue activo
            if hasattr(request.user, 'perfil') and not request.user.perfil.activo:
                # Cerrar sesión si el usuario fue desactivado
                from django.contrib.auth import logout
                logout(request)
                messages.warning(request, 'Su cuenta ha sido desactivada.')
                return redirect('login')
            
            # Renovar sesión para usuarios activos
            if not request.session.get('session_security_check'):
                request.session['session_security_check'] = True
                request.session['last_activity'] = str(timezone.now())
            
            # Actualizar última actividad cada 5 minutos
            last_activity = request.session.get('last_activity')
            if last_activity:
                from django.utils import timezone
                from datetime import timedelta
                import datetime
                
                last_time = datetime.datetime.fromisoformat(last_activity)
                if timezone.now() - last_time > timedelta(minutes=5):
                    request.session['last_activity'] = str(timezone.now())
            
        except Exception as e:
            logger.error(f'Error en middleware de seguridad: {e}')
        
        return None


class SucursalMiddleware(MiddlewareMixin):
    """
    Middleware para manejar automáticamente la sucursal activa
    """
    
    def process_request(self, request):
        """Verificar y configurar sucursal activa"""
        
        if not request.user.is_authenticated:
            return None
        
        # Verificar si hay una sucursal activa en sesión
        sucursal_id = request.session.get('sucursal_id')
        
        if not sucursal_id:
            # Asignar sucursal por defecto
            from .models import Sucursal
            
            # Primero intentar con la sucursal asignada al usuario
            if hasattr(request.user, 'perfil') and request.user.perfil.sucursal_asignada:
                sucursal = request.user.perfil.sucursal_asignada
                if sucursal.activa:
                    request.session['sucursal_id'] = sucursal.id
                    request.session['sucursal_nombre'] = sucursal.nombre
                    return None
            
            # Si no tiene asignada, usar la primera disponible
            sucursal = Sucursal.objects.filter(activa=True).first()
            if sucursal:
                request.session['sucursal_id'] = sucursal.id
                request.session['sucursal_nombre'] = sucursal.nombre
        else:
            # Verificar que la sucursal en sesión sigue activa
            from .models import Sucursal
            try:
                sucursal = Sucursal.objects.get(id=sucursal_id, activa=True)
                # Actualizar nombre por si cambió
                request.session['sucursal_nombre'] = sucursal.nombre
            except Sucursal.DoesNotExist:
                # Sucursal ya no existe o está inactiva, limpiar sesión
                if 'sucursal_id' in request.session:
                    del request.session['sucursal_id']
                if 'sucursal_nombre' in request.session:
                    del request.session['sucursal_nombre']
        
        return None


# =================
# DECORADOR ADICIONAL PARA VISTAS QUE REQUIEREN VERIFICACIÓN EXTRA
# =================

from functools import wraps
from django.core.exceptions import PermissionDenied

def verificar_propietario_o_admin(view_func):
    """
    Decorador que verifica que el usuario sea el propietario del recurso o administrador
    Útil para operaciones como editar perfil propio
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        
        # Si es administrador, puede acceder a todo
        if request.user.perfil.rol == 'administrador':
            return view_func(request, *args, **kwargs)
        
        # Si es el mismo usuario, puede acceder
        if user_id and str(request.user.id) == str(user_id):
            return view_func(request, *args, **kwargs)
        
        # Si no es ni admin ni propietario, denegar acceso
        raise PermissionDenied("No tiene permisos para acceder a este recurso.")
    
    return wrapped_view

def log_accion(accion_nombre):
    """
    Decorador para registrar acciones específicas en auditoría
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Ejecutar vista
            response = view_func(request, *args, **kwargs)
            
            # Registrar en auditoría si fue exitosa
            if hasattr(response, 'status_code') and response.status_code < 400:
                try:
                    logger.info(
                        f'ACCION: {request.user.username} ejecutó {accion_nombre}',
                        extra={
                            'user_id': request.user.id,
                            'accion': accion_nombre,
                            'url': request.path,
                            'metodo': request.method,
                            'kwargs': kwargs,
                        }
                    )
                except Exception as e:
                    logger.error(f'Error registrando acción {accion_nombre}: {e}')
            
            return response
        return wrapped_view
    return decorator


# =================
# UTILIDADES PARA AUDITORÍA
# =================

class AuditoriaUtils:
    """Utilidades para el sistema de auditoría"""
    
    @staticmethod
    def obtener_logs_usuario(user_id, limit=50):
        """Obtener logs de auditoría de un usuario específico"""
        import os
        logs = []
        
        try:
            log_file = 'logs/inventario.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    
                # Filtrar líneas que contengan el user_id
                user_lines = [line for line in lines if f'user_id": {user_id}' in line]
                
                # Tomar las últimas `limit` líneas
                logs = user_lines[-limit:] if len(user_lines) > limit else user_lines
        
        except Exception as e:
            logger.error(f'Error obteniendo logs de usuario {user_id}: {e}')
        
        return logs
    
    @staticmethod
    def obtener_estadisticas_auditoria(dias=30):
        """Obtener estadísticas de auditoría de los últimos días"""
        import os
        from datetime import datetime, timedelta
        
        stats = {
            'total_acciones': 0,
            'usuarios_activos': set(),
            'acciones_por_tipo': {},
            'acciones_por_dia': {},
        }
        
        try:
            log_file = 'logs/inventario.log'
            if os.path.exists(log_file):
                cutoff_date = datetime.now() - timedelta(days=dias)
                
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'AUDITORIA:' in line:
                            # Extraer información básica
                            stats['total_acciones'] += 1
                            
                            # Aquí se podría parsear más información del log
                            # según el formato específico implementado
        
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas de auditoría: {e}')
        
        return stats