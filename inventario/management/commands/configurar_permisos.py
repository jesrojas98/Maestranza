from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from inventario.models import crear_grupos_y_permisos, PerfilUsuario

class Command(BaseCommand):
    help = 'Configura grupos, permisos y crea usuario administrador inicial'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-admin',
            action='store_true',
            help='Crear usuario administrador inicial',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario para el administrador',
            default='admin'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email para el administrador',
            default='admin@ferreteria.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña para el administrador',
            default='admin123'
        )

    def handle(self, *args, **options):
        self.stdout.write('🔧 Configurando sistema de permisos...')
        
        # Crear grupos y permisos
        try:
            crear_grupos_y_permisos()
            self.stdout.write(
                self.style.SUCCESS('✅ Grupos y permisos creados exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando grupos: {e}')
            )
            return

        # Crear perfiles para usuarios existentes sin perfil
        usuarios_sin_perfil = User.objects.filter(perfil__isnull=True)
        for user in usuarios_sin_perfil:
            rol = 'administrador' if user.is_superuser else 'usuario_lectura'
            PerfilUsuario.objects.create(
                user=user,
                rol=rol,
                activo=user.is_active
            )
            self.stdout.write(f'📝 Perfil creado para {user.username}: {rol}')

        # Crear usuario administrador inicial si se solicita
        if options['crear_admin']:
            username = options['username']
            email = options['email']
            password = options['password']
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Usuario {username} ya existe')
                )
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name='Administrador',
                    last_name='Sistema',
                    is_staff=True,
                    is_superuser=True
                )
                
                # Configurar perfil
                user.perfil.rol = 'administrador'
                user.perfil.activo = True
                user.perfil.save()
                
                # Asignar a grupo
                admin_group = Group.objects.get(name='Administradores')
                user.groups.add(admin_group)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Usuario administrador creado: {username}'
                    )
                )
                self.stdout.write(f'📧 Email: {email}')
                self.stdout.write(f'🔑 Contraseña: {password}')

        self.stdout.write(
            self.style.SUCCESS('🎉 Configuración completada exitosamente!')
        )
