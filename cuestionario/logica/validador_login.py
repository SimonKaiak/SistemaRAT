"""
validador_login.py
--------------
Vistas de autenticación del sistema: login y logout.

login_view(request)
    Maneja el inicio de sesión permitiendo el acceso a superusuarios
    y trabajadores con perfil asociado.

    Flujo:
    - Si el usuario ya está autenticado, redirige a index.
    - Recibe correo y contraseña por POST.
    - Busca el User por email para obtener su username, ya que
      Django autentica por username internamente.
    - Si las credenciales son válidas:
        - Superusuario: accede directamente a index.
        - Usuario con perfil Trabajador: accede a index.
        - Usuario sin perfil Trabajador: se hace logout y se
          muestra error "no tiene perfil de Trabajador asociado".
    - Si las credenciales son inválidas, muestra error.
    Template: login.html

logout_view(request)
    Cierra la sesión del usuario y redirige a la vista de login.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from cuestionario.models import Trabajador
from django.contrib.auth.models import User

def login_view(request):
    """
    Maneja la autenticación permitiendo el paso a Superusuarios y Trabajadores.
    """
    error_message = None
    
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        correo = request.POST.get('username')
        clave = request.POST.get('password')
        
        try:
            user_obj = User.objects.filter(email=correo).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=clave)
            else:
                user = None
        except Exception:
            user = None
        
        if user is not None:
            login(request, user)
            
            # Si es Admin, entra directo. Si no, verifica si es Trabajador.
            if user.is_superuser:
                return redirect('index')
            
            try:
                Trabajador.objects.get(user=user)
                return redirect('index')
            except Trabajador.DoesNotExist:
                # Si no es admin y no tiene perfil, lo sacamos
                logout(request)
                error_message = "Usuario válido, pero no tiene perfil de Trabajador asociado."
        else:
            error_message = "Correo o contraseña incorrectos."
            
    context = {'error': error_message}
    return render(request, 'cuestionario/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')