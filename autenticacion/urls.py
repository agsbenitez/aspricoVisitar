from django.urls import path
from .views import CustomLoginView

app_name = 'autenticacion'

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
]