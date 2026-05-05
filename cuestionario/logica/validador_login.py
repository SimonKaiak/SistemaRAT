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
            user_obj = User.objects.get(email=correo)
            user = authenticate(request, username=user_obj.username, password=clave)
        except User.DoesNotExist:
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