import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Maestranza.settings')
django.setup()

from django.core.management import call_command

def instalar_sistema_permisos():
    print("🚀 Iniciando instalación del sistema de permisos...")
    
    # 1. Crear migraciones
    print("\n📝 Creando migraciones...")
    call_command('makemigrations', 'inventario')
    
    # 2. Aplicar migraciones
    print("\n🔄 Aplicando migraciones...")
    call_command('migrate')
    
    # 3. Configurar permisos
    print("\n🔧 Configurando permisos y grupos...")
    call_command('configurar_permisos')
    
    # 4. Crear administrador
    print("\n👤 ¿Desea crear un usuario administrador? (s/n): ", end="")
    crear_admin = input().lower().startswith('s')
    
    if crear_admin:
        username = input("Nombre de usuario [admin]: ") or "admin"
        email = input("Email [admin@ferreteria.com]: ") or "admin@ferreteria.com"
        password = input("Contraseña [admin123]: ") or "admin123"
        
        call_command('configurar_permisos', 
                    crear_admin=True,
                    username=username,
                    email=email,
                    password=password)
    
    print("\n🎉 ¡Sistema de permisos instalado exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Inicia el servidor: python manage.py runserver")
    print("2. Ve a /admin/ para configurar sucursales y categorías")
    print("3. Accede al sistema con las credenciales del administrador")
    print("4. Crea usuarios adicionales desde el panel de administración")

if __name__ == "__main__":
    instalar_sistema_permisos()