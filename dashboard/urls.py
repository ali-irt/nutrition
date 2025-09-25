from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('lead/', views.lead, name='lead'),
    path('client/<int:client_id>/', views.client_profile, name='client_profile'),
    path('nutrition/', views.nutrition, name='nutrition'),
    path('workouts/', views.workouts, name='workouts'),
    path('content/', views.content, name='content'),
    path('meals/', views.meals, name='meals'),
    path('clients/', views.clients_active, name='clients_active'),
    path('clients/started/', views.clients_started, name='started_clients'),
    path('clients/completed/', views.clients_completed, name='ended_clients'),
]

