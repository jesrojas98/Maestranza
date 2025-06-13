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
            '--arreglar-admin',
            action='store_true',
            help='Arreglar perfil del usuario admin existente',
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

        # Arreglar usuario admin existente
        if options['arreglar_admin'] or options['crear_admin']:
            username = options['username']
            
            try:
                # Buscar usuario admin existente
                admin_user = User.objects.get(username=username)
                self.stdout.write(f'👤 Usuario {username} encontrado')
                
                # Asegurar que es superuser
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                
                # Crear o actualizar perfil
                perfil, created = PerfilUsuario.objects.get_or_create(
                    user=admin_user,
                    defaults={
                        'rol': 'administrador',
                        'activo': True
                    }
                )
                
                if not created:
                    perfil.rol = 'administrador'
                    perfil.activo = True
                    perfil.save()
                
                # Asignar a grupo administradores
                try:
                    admin_group = Group.objects.get(name='Administradores')
                    admin_user.groups.add(admin_group)
                    self.stdout.write(f'👥 Usuario agregado al grupo Administradores')
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING('⚠️ Grupo Administradores no encontrado'))
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario {username} configurado como administrador')
                )
                
            except User.DoesNotExist:
                if options['crear_admin']:
                    # Crear nuevo usuario admin
                    email = options['email']
                    password = options['password']
                    
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
                    PerfilUsuario.objects.create(
                        user=user,
                        rol='administrador',
                        activo=True
                    )
                    
                    # Asignar a grupo
                    admin_group = Group.objects.get(name='Administradores')
                    user.groups.add(admin_group)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Usuario administrador creado: {username}')
                    )

        self.stdout.write(
            self.style.SUCCESS('🎉 Configuración completada exitosamente!')
        )