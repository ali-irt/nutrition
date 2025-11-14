# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import *



 
router = DefaultRouter()

# Register viewsets
router.register(r'profile', views.UserProfileViewSet, basename='profile')
router.register(r'foods', views.FoodViewSet, basename='food')
router.register(r'food-diary', views.FoodDiaryViewSet, basename='food-diary')
router.register(r'workouts', views.WorkoutViewSet, basename='workout')
router.register(r'exercises', views.ExerciseViewSet, basename='exercise')
router.register(r'workout-logs', views.UserWorkoutLogViewSet, basename='workout-log')
router.register(r'progress', views.ProgressViewSet, basename='progress')
router.register(r'water', views.WaterLogViewSet, basename='water')
router.register(r'activity', views.DailyActivityViewSet, basename='activity')
router.register(r'checkin-forms', views.CheckinFormViewSet, basename='checkin-form')
router.register(r'checkins', views.CheckinViewSet, basename='checkin')
router.register(r'plans', views.PlanViewSet, basename='plan')
router.register(r'addresses', views.AddressViewSet, basename='address')
router.register(r'meal-subscriptions', views.MealSubscriptionViewSet, basename='meal-subscription')
router.register(r'meals', views.MealViewSet, basename='meal')
router.register(r'orders', views.MealOrderViewSet, basename='order')
router.register(r'deliveries', views.DeliveryViewSet, basename='delivery')
router.register(r'cardio', views.CardioSessionViewSet, basename='cardio')
router.register(r'heart-rate', views.HeartRateViewSet, basename='heart-rate')
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'macro-plans', views.MacroPlanViewSet, basename='macro-plan')
router.register(r'daily-targets', views.DailyMacroTargetViewSet, basename='daily-target')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'chat-threads', views.ChatThreadViewSet, basename='chat-thread')
router.register(r'messages', views.ChatMessageViewSet, basename='chatmessage')
router.register(r'meal-box', views.MealBoxViewSet, basename='meal-box')

router.register(r'chat-messages', views.ChatMessageViewSet, basename='chat-message')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')
router.register(r'files', views.UserFileViewSet, basename='file')

urlpatterns = [
    # Auth endpoints
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('auth/register/', views.Register, name='register'),
    path('auth/login/', views.Login, name='login'),
    path('auth/send-otp/', views.send_otp, name='send-otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify-otp'),
    path('meal-workflow/<str:step>/', MealWorkflowView.as_view(), name='meal-workflow'),
    path('auth/forgot-password/', views.forgot_password, name='forgot-password'),  # 👈 Add this line
    path('auth/reset-password/', views.reset_password, name='reset-password'),  # 👈 Add this lin e
    # Dashboard endpoints
    path('dashboard/today/', views.dashboard_today, name='dashboard-today'),
    path('dashboard/weekly-progress/', views.weekly_progress, name='weekly-progress'),


    # Analytics endpoints
   path('analytics/weekly/', views.weekly_analytics, name='analytics-weekly'),
   path('analytics/monthly/', views.monthly_analytics, name='analytics-monthly'),
    
    # Notification endpoints
   path('notifications/register-device/', views.register_push_token, name='register-push-token'),
    
    # Coach/Admin endpoints
   path('coach/clients/', views.list_clients, name='list-clients'),
   path('coach/clients/<int:client_id>/', views.client_detail, name='client-detail'),
   path('coach/clients/<int:client_id>/assign-workout/', views.assign_workout_to_client, name='assign-workout'),
 # Cart
    path('cart/', get_cart, name='get-cart'),
    path('cart/add/', add_to_cart, name='add-to-cart'),
    path('cart/items/<int:item_id>/', update_cart_item, name='update-cart-item'),
    path('cart/items/<int:item_id>/delete/', remove_cart_item, name='remove-cart-item'),
    path('cart/clear/', clear_cart, name='clear-cart'),
    
    # Address
    path('addresses/', get_addresses, name='get-addresses'),
    path('validate-shipping/', validate_shipping, name='validate-shipping'),
    
    # Payment
    path('payment-methods/', get_payment_methods, name='payment-methods'),
    path('process-payment/', process_payment, name='process-payment'),
    
    # Order
     path('orders/', get_orders, name='get-orders'),
    path('orders/<int:order_id>/', get_order_detail, name='order-detail'),
    # Include router URLs
    path('', include(router.urls)),
]
