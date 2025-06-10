from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import LoginForm

# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm
    #redirect_authenticated_user = True

    def form_invalid(self, form):

        form.add_error(None, 'El nombre de usuario o la contraseña son incorrectos.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        # Redirige a una URL específica después del inicio de sesión exitoso
        return reverse_lazy('home')  