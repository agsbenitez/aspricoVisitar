from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy


def error_404_view(request, exception):
    data = {}
    return render(request,'error_404.html', data)

def error_403_view(request, exception):
    return render(request, 'error_403.html', {'exception': exception})

class CustomLoginView(LoginView):
    template_name = 'login.html'
    #redirect_authenticated_user = True

    def form_invalid(self, form):
        print("tratando de Loguarme")

        form.add_error(None, 'El nombre de usuario o la contraseña son incorrectos.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        # Redirige a una URL específica después del inicio de sesión exitoso
        return reverse_lazy('home')  # Cambia 'home' por el nombre de tu URL