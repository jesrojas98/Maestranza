from django import forms
from django.core.exceptions import ValidationError
from .models import *
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PerfilUsuario, Sucursal
from django.core.exceptions import ValidationError
import re

class ProductoForm(forms.ModelForm):
    UNIDADES_MEDIDA = [
        ('unidad', 'Unidad'),
        ('metro', 'Metro'),
        ('kilogramo', 'Kilogramo'),
        ('litro', 'Litro'),
    ]
    unidad_medida = forms.ChoiceField(
        choices=UNIDADES_MEDIDA,
        initial='unidad',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'imagen', 'etiquetas',
            'precio',  # ✅ Campo agregado
            'unidad_medida', 'stock_minimo', 'maneja_lotes', 
            'maneja_vencimiento', 'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del producto'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del producto'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'etiquetas': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            # ✅ Widget para precio
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '1',
                'min': '0'
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: unidad, metro, kilogramo'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'maneja_lotes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'maneja_vencimiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = "Selecciona una categoría"
        self.fields['etiquetas'].queryset = Etiqueta.objects.all()

        self.fields['imagen'].widget.attrs.update({
            'class': 'd-none',
            'accept': 'image/*'
        })

        # Marcar campos requeridos
        self.fields['codigo'].required = True
        self.fields['nombre'].required = True
        # ✅ Precio opcional
        self.fields['precio'].required = False

        # Ayudas contextuales
        self.fields['maneja_lotes'].help_text = "Permite registrar lotes con códigos y fechas específicas"
        self.fields['maneja_vencimiento'].help_text = "Controla fechas de vencimiento y genera alertas"
        # ✅ Ayuda para precio
        self.fields['precio'].help_text = "Precio base del producto (opcional)"

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        return codigo.upper()

    # ✅ Validación para precio
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean(self):
        cleaned_data = super().clean()
        maneja_lotes = cleaned_data.get('maneja_lotes')
        maneja_vencimiento = cleaned_data.get('maneja_vencimiento')

        # Si maneja vencimiento, debe manejar lotes
        if maneja_vencimiento and not maneja_lotes:
            cleaned_data['maneja_lotes'] = True
            self.add_error('maneja_vencimiento',
                           'Para manejar vencimientos, el producto debe manejar lotes.')

        return cleaned_data

class PrecioProductoForm(forms.ModelForm):
    precio = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0',
            'step': '1',
            'min': '1'
        }),
        help_text="Nuevo precio del producto"
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo del cambio de precio (opcional)'
        }),
        help_text="Observaciones sobre el cambio de precio"
    )
    
    class Meta:
        model = Producto
        fields = ['precio']

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = [
            'sucursal', 'tipo', 'cantidad', 'sucursal_destino',
            'lote', 'motivo', 'numero_documento'
        ]
        widgets = {
            'sucursal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'sucursal_destino': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lote': forms.Select(attrs={
                'class': 'form-select'
            }),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo del movimiento'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura, orden, etc.'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
            
        # Configurar queryset para sucursales activas
        self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)
        self.fields['sucursal_destino'].queryset = Sucursal.objects.filter(activa=True)
        
        # Configurar lotes si el producto maneja lotes
        if self.producto and self.producto.maneja_lotes:
            self.fields['lote'].queryset = Lote.objects.filter(producto=self.producto)
            self.fields['lote'].widget.attrs['class'] = 'form-select'
        else:
            self.fields['lote'].widget = forms.HiddenInput()
        
        # Labels personalizados
        self.fields['sucursal'].empty_label = "Selecciona una sucursal"
        self.fields['sucursal_destino'].empty_label = "Selecciona sucursal destino"
        self.fields['lote'].empty_label = "Selecciona un lote (opcional)"
        self.fields['sucursal_destino'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad = cleaned_data.get('cantidad')
        
        # Validar transferencias
        if tipo == 'transferencia':
            if not sucursal_destino:
                raise ValidationError('Debe seleccionar una sucursal destino para transferencias.')
            if sucursal == sucursal_destino:
                raise ValidationError('La sucursal origen y destino no pueden ser la misma.')
        
        # Validar cantidad positiva
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')
        
        return cleaned_data

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'contacto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona de contacto'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@proveedor.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa del proveedor'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['codigo', 'fecha_vencimiento', 'proveedor', 'precio_compra']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del lote'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'proveedor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
        self.fields['proveedor'].empty_label = "Selecciona un proveedor"
        self.fields['fecha_vencimiento'].required = False
        
        # Labels personalizados
        self.fields['codigo'].label = 'Código del Lote'
        self.fields['fecha_vencimiento'].label = 'Fecha de Vencimiento'
        self.fields['proveedor'].label = 'Proveedor'
        self.fields['precio_compra'].label = 'Precio de Compra'
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        # Verificar que el código no existe para el mismo producto
        if hasattr(self, 'instance') and hasattr(self.instance, 'producto'):
            if Lote.objects.filter(
                codigo=codigo, 
                producto=self.instance.producto
            ).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Ya existe un lote con este código para este producto.')
        return codigo.upper()    

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }

class EtiquetaForm(forms.ModelForm):
    class Meta:
        model = Etiqueta
        fields = ['nombre', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la etiqueta'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        return nombre.title()  # Capitalizar primera letra

class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['nombre', 'direccion', 'telefono', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la sucursal'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa de la sucursal'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 2 1234 5678'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class BusquedaForm(forms.Form):
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar productos...',
            'autocomplete': 'off'
        })
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activa=True),
        required=False,
        empty_label="Todas las sucursales",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class ReporteForm(forms.Form):
    TIPO_REPORTE_CHOICES = [
        ('stock', 'Reporte de Stock'),
        ('movimientos', 'Reporte de Movimientos'),
        ('alertas', 'Reporte de Alertas'),
        ('vencimientos', 'Productos por Vencer'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_REPORTE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activa=True),
        required=False,
        empty_label="Todas las sucursales",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = [
            'sucursal', 'tipo', 'cantidad', 'sucursal_destino',
            'motivo', 'numero_documento'
        ]
        widgets = {
            'sucursal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'sucursal_destino': forms.Select(attrs={
                'class': 'form-select'
            }),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo del movimiento'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura, orden, etc.'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para sucursales activas
        self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)
        self.fields['sucursal_destino'].queryset = Sucursal.objects.filter(activa=True)
        
        # Labels personalizados
        self.fields['sucursal'].empty_label = "Selecciona una sucursal"
        self.fields['sucursal_destino'].empty_label = "Selecciona sucursal destino"
        
        # Configurar campo sucursal_destino según el tipo
        self.fields['sucursal_destino'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad = cleaned_data.get('cantidad')
        
        # Validar transferencias
        if tipo == 'transferencia':
            if not sucursal_destino:
                raise forms.ValidationError('Debe seleccionar una sucursal destino para transferencias.')
            if sucursal == sucursal_destino:
                raise forms.ValidationError('La sucursal origen y destino no pueden ser la misma.')
        
        # Validar cantidad positiva
        if cantidad and cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a cero.')
        
        return cleaned_data    
class ReporteForm(forms.Form):
    TIPO_REPORTE_CHOICES = [
        ('stock', 'Reporte de Stock'),
        ('movimientos', 'Reporte de Movimientos'),
        ('alertas', 'Reporte de Alertas'),
        ('vencimientos', 'Productos por Vencer'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_REPORTE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Reporte'
    )
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activa=True),
        required=False,
        empty_label="Todas las sucursales",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Sucursal'
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Desde'
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Hasta'
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Categoría'
    )    

class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['codigo', 'nombre', 'tipo', 'descripcion', 'capacidad_maxima', 'activa']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: A-01, B-15, BOD-1'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pasillo A - Estante 1'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la ubicación'
            }),
            'capacidad_maxima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Cantidad máxima de productos'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.sucursal = kwargs.pop('sucursal', None)
        super().__init__(*args, **kwargs)
        
        # Labels personalizados
        self.fields['codigo'].label = 'Código de Ubicación'
        self.fields['nombre'].label = 'Nombre Descriptivo'
        self.fields['tipo'].label = 'Tipo de Ubicación'
        self.fields['descripcion'].label = 'Descripción'
        self.fields['capacidad_maxima'].label = 'Capacidad Máxima'
        self.fields['activa'].label = 'Ubicación Activa'
        
        # Ayudas contextuales
        self.fields['codigo'].help_text = "Código único dentro de la sucursal"
        self.fields['capacidad_maxima'].help_text = "Opcional - Para control de ocupación"
        self.fields['activa'].help_text = "Las ubicaciones inactivas no aparecen en selecciones"
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].upper()
        
        # Verificar unicidad en la sucursal
        if self.sucursal:
            existing = Ubicacion.objects.filter(
                sucursal=self.sucursal,
                codigo=codigo
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe una ubicación con el código "{codigo}" en esta sucursal.'
                )
        
        return codigo

class AsignarUbicacionForm(forms.ModelForm):
    """Formulario para asignar ubicación a un inventario"""
    class Meta:
        model = Inventario
        fields = ['ubicacion_detallada']
        widgets = {
            'ubicacion_detallada': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        sucursal = kwargs.pop('sucursal', None)
        super().__init__(*args, **kwargs)
        
        if sucursal:
            self.fields['ubicacion_detallada'].queryset = Ubicacion.objects.filter(
                sucursal=sucursal,
                activa=True
            ).order_by('tipo', 'codigo')
        else:
            self.fields['ubicacion_detallada'].queryset = Ubicacion.objects.none()
        
        self.fields['ubicacion_detallada'].empty_label = "Seleccionar ubicación"
        self.fields['ubicacion_detallada'].label = "Nueva Ubicación"
        self.fields['ubicacion_detallada'].required = False

# Actualizar MovimientoForm para incluir ubicaciones
class MovimientoForm(forms.ModelForm):
    ubicacion_destino = forms.ModelChoiceField(
        queryset=Ubicacion.objects.none(),
        required=False,
        empty_label="Mantener ubicación actual",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Ubicación Destino",
        help_text="Opcional - Cambiar ubicación del producto"
    )
    
    class Meta:
        model = MovimientoInventario
        fields = [
            'sucursal', 'tipo', 'cantidad', 'sucursal_destino',
            'motivo', 'numero_documento'
        ]
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'sucursal_destino': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo del movimiento'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura, orden, etc.'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para sucursales activas
        self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)
        self.fields['sucursal_destino'].queryset = Sucursal.objects.filter(activa=True)
        
        # Configurar lotes si el producto maneja lotes
        if self.producto and self.producto.maneja_lotes:
            # Agregar campo lote si no existe
            if 'lote' not in self.fields:
                self.fields['lote'] = forms.ModelChoiceField(
                    queryset=Lote.objects.filter(producto=self.producto),
                    required=False,
                    empty_label="Selecciona un lote (opcional)",
                    widget=forms.Select(attrs={'class': 'form-select'})
                )
        
        # Labels personalizados
        self.fields['sucursal'].empty_label = "Selecciona una sucursal"
        self.fields['sucursal_destino'].empty_label = "Selecciona sucursal destino"
        self.fields['sucursal_destino'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        sucursal = cleaned_data.get('sucursal')
        sucursal_destino = cleaned_data.get('sucursal_destino')
        cantidad = cleaned_data.get('cantidad')
        
        # Validar transferencias
        if tipo == 'transferencia':
            if not sucursal_destino:
                raise forms.ValidationError('Debe seleccionar una sucursal destino para transferencias.')
            if sucursal == sucursal_destino:
                raise forms.ValidationError('La sucursal origen y destino no pueden ser la misma.')
        
        # Validar cantidad positiva
        if cantidad and cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a cero.')
        
        return cleaned_data

class CrearUsuarioForm(forms.ModelForm):
    """Formulario para crear nuevos usuarios con perfil"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña segura'
        }),
        help_text='Mínimo 8 caracteres, debe incluir letras y números'
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        label='Confirmar contraseña'
    )
    
    rol = forms.ChoiceField(
        choices=PerfilUsuario.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_rol'
        }),
        help_text='Seleccione el rol que tendrá el usuario en el sistema'
    )
    
    sucursal_asignada = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activa=True),
        required=False,
        empty_label="Sin sucursal específica",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Sucursal principal donde trabajará el usuario'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario único'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
        }
        help_texts = {
            'username': 'Solo letras, números y los caracteres @/./+/-/_',
            'email': 'Dirección de correo electrónico válida',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos obligatorios
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya existe.')
        
        # Validar formato
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('El nombre de usuario solo puede contener letras, números y los caracteres @/./+/-/_')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_password(self):
        password = self.cleaned_data['password']
        
        # Validaciones de contraseña
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data

class EditarUsuarioForm(forms.ModelForm):
    """Formulario para editar usuarios existentes"""
    
    rol = forms.ChoiceField(
        choices=PerfilUsuario.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    sucursal_asignada = forms.ModelChoiceField(
        queryset=Sucursal.objects.filter(activa=True),
        required=False,
        empty_label="Sin sucursal específica",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    activo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        help_text='Usuario activo en el sistema'
    )
    
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña (opcional)'
        }),
        help_text='Dejar en blanco para mantener la contraseña actual'
    )
    
    new_password_confirm = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        label='Confirmar nueva contraseña'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos obligatorios
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        
        # Pre-llenar campo activo con el estado del perfil
        if self.instance and hasattr(self.instance, 'perfil'):
            self.fields['activo'].initial = self.instance.perfil.activo
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Excluir el usuario actual de la validación
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        
        if password:  # Solo validar si se proporcionó una nueva contraseña
            if len(password) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
            
            if not re.search(r'[A-Za-z]', password):
                raise ValidationError('La contraseña debe contener al menos una letra.')
            
            if not re.search(r'\d', password):
                raise ValidationError('La contraseña debe contener al menos un número.')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        
        # Solo validar coincidencia si se está cambiando la contraseña
        if new_password or new_password_confirm:
            if new_password != new_password_confirm:
                raise ValidationError('Las nuevas contraseñas no coinciden.')
        
        return cleaned_data

class FiltroUsuariosForm(forms.Form):
    """Formulario para filtrar la lista de usuarios"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, usuario o email...',
        }),
        label='Búsqueda'
    )
    
    rol = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los roles')] + PerfilUsuario.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    activo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    sucursal = forms.ModelChoiceField(
        required=False,
        queryset=Sucursal.objects.filter(activa=True),
        empty_label="Todas las sucursales",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class CambiarPasswordForm(forms.Form):
    """Formulario para que los usuarios cambien su propia contraseña"""
    
    password_actual = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        }),
        label='Contraseña actual'
    )
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        label='Nueva contraseña',
        help_text='Mínimo 8 caracteres, debe incluir letras y números'
    )
    
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        label='Confirmar nueva contraseña'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password_actual(self):
        password_actual = self.cleaned_data['password_actual']
        if not self.user.check_password(password_actual):
            raise ValidationError('La contraseña actual es incorrecta.')
        return password_actual
    
    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra.')
        
        if not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        
        if new_password and new_password_confirm:
            if new_password != new_password_confirm:
                raise ValidationError('Las nuevas contraseñas no coinciden.')
        
        return cleaned_data