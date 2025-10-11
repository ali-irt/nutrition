from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Home
    path("", views.dashboard_home, name="dashboard_home"),

    path("leads/", views.leads_all, name="leads_all"),
    path("leads/new/", views.leads_new, name="leads_new"),
    path("leads/contacted/", views.leads_contacted, name="leads_contacted"),
    path("leads/dialogue/", views.leads_dialogue, name="leads_dialogue"),
    path("leads/onhold/", views.leads_onhold, name="leads_onhold"),
    path("leads/won/", views.leads_won, name="leads_won"),
    path("leads/lost/", views.leads_lost, name="leads_lost"),
# urls.py - Fix these patterns

    path("delete/<int:pk>/", views.delete_lead, name="delete_lead"),
    path("clients/active/", views.clients_active, name="clients_active"),
    path("clients/payment-error/", views.clients_payment_error, name="clients_payment_error"),
    path("clients/just-started/", views.clients_started, name="clients_started"),  # Changed from clients_started
    path("clients/new-message/", views.clients_new_message, name="clients_new_message"),
    path("clients/new-checkin/", views.clients_new_checkin, name="clients_new_checkin"),
    path("clients/missed-checkin/", views.clients_missed_checkin, name="clients_missed_checkin"),
    path("clients/reminders/", views.clients_reminders, name="clients_reminders"),
    path("clients/ending/", views.clients_completed, name="clients_completed"),  # Changed from clients_completed
    path("clients/no-communication/", views.clients_no_communication, name="clients_no_communication"),
    path("clients/offer-sent/", views.clients_offer_sent, name="clients_offer_sent"),
    path("clients/no-account/", views.clients_no_account, name="clients_no_account"),
    path("client/<int:client_id>/", views.client_profile, name="client_profile"),
   path("client/<int:client_id>/workout/", views.client_workout, name="client_workout"),
   path("client/<int:client_id>/progress/", views.client_progress, name="client_progress"),
    path("client/<int:client_id>/nutrition/", views.client_nutrition, name="client_nutrition"),
    path("nutrition/recipes/", views.nutrition_recipes, name="nutrition_recipes"),
    path("nutrition/templates/", views.nutrition_templates, name="nutrition_templates"),
    path("nutrition/", views.nutrition, name="nutrition"),
    path("nutrition/ingredients/create/", views.ingredient_create, name="ingredient_create"), 
    path("nutrition/recipes/create/", views.recipe_create, name="recipe_create"),
    path("nutrition/templates/create/", views.nutrition_template_create, name="nutrition_template_create"),
    path("workouts/", views.workouts, name="workouts"),
    path("workouts/templates/<int:pk>/", views.template_detail, name="workout_template_detail"),
    path("workouts/templates/<int:pk>/add-session/", views.template_add_session, name="workout_template_add_session"),
    path("workouts/templates/<int:pk>/rename/", views.template_rename, name="workout_template_rename"),
    path("workouts/templates/<int:pk>/add-session/", views.template_add_session, name="workout_template_add_session"),
    # Existing editor endpoints (can stay as-is)
    path("workouts/new/", views.workout_new, name="workout_new"),
    path("workouts/<int:pk>/edit/", views.workout_edit, name="workout_edit"),
    path("workouts/<int:pk>/delete/", views.workout_delete, name="workout_delete"),
    path("workouts/<int:pk>/toggle-complete/", views.workout_toggle_complete, name="workout_toggle_complete"),
    path("workouts/<int:pk>/duplicate/", views.workout_duplicate, name="workout_duplicate"),
    # Progress
    path("progress/", views.progress_list, name="progress_list"),

    # Meals
    path("meals/", views.meals, name="meals"),

    # Wishlist
    path("wishlist/", views.wishlist_list, name="wishlist"),

    # Content
    path('content/', views.content, name='content'),

    # File CRUD
    path('add-file/', views.add_file, name='add_file'),
    path('edit-file/<int:pk>/', views.edit_file, name='edit_file'),
    path('delete-file/<int:pk>/', views.delete_file, name='delete_file'),

    # Lesson CRUD
    path('add-lesson/', views.add_lesson, name='add_lesson'),
    path('edit-lesson/<int:pk>/', views.edit_lesson, name='edit_lesson'),
    path('delete-lesson/<int:pk>/', views.delete_lesson, name='delete_lesson'),]