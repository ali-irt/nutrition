from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('client/<int:client_id>/', views.client_profile, name='client_profile'),
    path('workouts/', views.workouts, name='workouts'),
    path('content/', views.content, name='content'),
    path('meals/', views.meals, name='meals'),
    path('clients/started/', views.clients_started, name='started_clients'),
    path('clients/completed/', views.clients_completed, name='ended_clients'),

    #leads
      path("leads/", views.leads_all, name="leads_all"),
    path("leads/new/", views.leads_new, name="leads_new"),
    path("leads/contacted/", views.leads_contacted, name="leads_contacted"),
    path("leads/dialogue/", views.leads_dialogue, name="leads_dialogue"),
    path("leads/onhold/", views.leads_onhold, name="leads_onhold"),
    path("leads/won/", views.leads_won, name="leads_won"),
    path("leads/lost/", views.leads_lost, name="leads_lost"),
#clients
  path("clients/active/", views.clients_active, name="clients_active"),
    path("clients/payment-error/", views.clients_payment_error, name="clients_payment_error"),
    path("clients/just-started/", views.clients_just_started, name="clients_just_started"),
    path("clients/new-message/", views.clients_new_message, name="clients_new_message"),
    path("clients/new-checkin/", views.clients_new_checkin, name="clients_new_checkin"),
    path("clients/missed-checkin/", views.clients_missed_checkin, name="clients_missed_checkin"),
    path("clients/reminders/", views.clients_reminders, name="clients_reminders"),
    path("clients/ending/", views.clients_ending, name="clients_ending"),
    path("clients/no-communication/", views.clients_no_communication, name="clients_no_communication"),
    #nutrition
        path('nutrition/', views.nutrition, name='nutrition'),

    path('nutrition/recipes/', views.nutrition_recipes, name='nutrition_recipes'),
    path('nutrition/templates/', views.nutrition_templates, name='nutrition_templates'),
]


