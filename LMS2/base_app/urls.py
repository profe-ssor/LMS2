from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('password-reset/', views.request_password_reset, name='password-reset'),
    path('password-reset-confirm/<str:uid>/<str:token>/', views.reset_password, name='password-reset-confirm'),
]
