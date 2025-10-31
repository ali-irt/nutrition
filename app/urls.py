# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
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
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='payment-method')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'chat-threads', views.ChatThreadViewSet, basename='chat-thread')
router.register(r'messages', views.ChatMessageViewSet, basename='chatmessage')

router.register(r'chat-messages', views.ChatMessageViewSet, basename='chat-message')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')
router.register(r'files', views.UserFileViewSet, basename='file')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.Register, name='register'),
    path('auth/login/', views.Login, name='login'),
    path('auth/send-otp/', views.send_otp, name='send-otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify-otp'),
    
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

    # Include router URLs
    path('', include(router.urls)),
]

"""
COMPLETE API ENDPOINT REFERENCE
================================

AUTHENTICATION
--------------
POST   /api/auth/register/              - Register new user
POST   /api/auth/login/                 - User login
POST   /api/auth/send-otp/              - Send OTP for verification
POST   /api/auth/verify-otp/            - Verify OTP code

PROFILE
-------
GET    /api/profile/                    - List profiles (current user)
GET    /api/profile/me/                 - Get current user profile
POST   /api/profile/create_profile/     - Create profile (onboarding)
PATCH  /api/profile/{id}/               - Update profile
GET    /api/profile/{id}/               - Get profile detail

DASHBOARD
---------
GET    /api/dashboard/today/            - Get today's dashboard summary
GET    /api/dashboard/weekly-progress/  - Get weekly progress

FOOD & MEALS
------------
GET    /api/foods/                      - Search foods (query: ?q=chicken)
GET    /api/foods/{id}/                 - Get food detail
POST   /api/foods/scan_barcode/         - Scan barcode (body: {barcode: "..."})

GET    /api/food-diary/                 - List food diary entries (query: ?date=2025-10-23)
GET    /api/food-diary/diary/           - Get meal diary for date (query: ?date=2025-10-23)
POST   /api/food-diary/                 - Log food/meal
PATCH  /api/food-diary/{id}/            - Update food entry
DELETE /api/food-diary/{id}/            - Delete food entry

GET    /api/meals/                      - List curated meals
GET    /api/meals/{id}/                 - Get meal detail
GET    /api/meals/menu/                 - Get weekly menu (query: ?week_start=2025-10-28)

WORKOUTS
--------
GET    /api/workouts/                   - List workouts (query: ?date=2025-10-23&status=scheduled)
POST   /api/workouts/                   - Create workout
GET    /api/workouts/{id}/              - Get workout detail
PATCH  /api/workouts/{id}/              - Update workout
DELETE /api/workouts/{id}/              - Delete workout

GET    /api/exercises/                  - List exercises (query: ?muscle_group=chest&search=press)
GET    /api/exercises/{id}/             - Get exercise detail
GET    /api/exercises/{id}/history/     - Get exercise history for user

GET    /api/workout-logs/               - List workout logs
POST   /api/workout-logs/               - Create workout log (start session)
GET    /api/workout-logs/{id}/          - Get workout log detail
POST   /api/workout-logs/{id}/log_set/  - Log a set
PATCH  /api/workout-logs/{id}/complete/ - Complete workout

PROGRESS
--------
GET    /api/progress/                   - List progress entries (query: ?from=2025-09-01&to=2025-10-23)
POST   /api/progress/                   - Add progress entry
GET    /api/progress/{id}/              - Get progress detail
GET    /api/progress/{id}/photos/       - Get progress photos

WATER & ACTIVITY
----------------
GET    /api/water/                      - List water logs
POST   /api/water/                      - Log water intake
GET    /api/water/today/                - Get today's water intake
DELETE /api/water/{id}/                 - Delete water log

GET    /api/activity/                   - List daily activities
POST   /api/activity/                   - Create activity summary
POST   /api/activity/sync_steps/        - Sync steps from device
GET    /api/activity/steps_today/       - Get today's steps (query: ?date=2025-10-23)

CHECK-INS
---------
GET    /api/checkin-forms/              - List available check-in forms
GET    /api/checkin-forms/{id}/         - Get form detail

GET    /api/checkins/                   - List user check-ins
POST   /api/checkins/                   - Submit check-in
GET    /api/checkins/{id}/              - Get check-in detail

CARDIO
------
GET    /api/cardio/                     - List cardio sessions (query: ?activity=run&from=2025-10-01)
POST   /api/cardio/                     - Start cardio session
GET    /api/cardio/{id}/                - Get session detail
PATCH  /api/cardio/{id}/                - Update session
PATCH  /api/cardio/{id}/finish/         - Finish session

HEART RATE
----------
GET    /api/heart-rate/                 - Get heart rate data (query: ?from=...&to=...)
POST   /api/heart-rate/                 - Log single HR sample
POST   /api/heart-rate/bulk/            - Bulk sync HR samples

RECIPES
-------
GET    /api/recipes/                    - List recipes (query: ?is_public=true&search=chicken)
POST   /api/recipes/                    - Create recipe
GET    /api/recipes/{id}/               - Get recipe detail
PATCH  /api/recipes/{id}/               - Update recipe
DELETE /api/recipes/{id}/               - Delete recipe

MACRO PLANS
-----------
GET    /api/macro-plans/                - List macro plans
POST   /api/macro-plans/                - Create macro plan
POST   /api/macro-plans/calculate/      - Calculate macros from profile
GET    /api/macro-plans/active/         - Get active macro plan
GET    /api/macro-plans/{id}/           - Get plan detail
PATCH  /api/macro-plans/{id}/           - Update plan

GET    /api/daily-targets/              - Get daily macro target (query: ?date=2025-10-23)

SUBSCRIPTIONS & MEAL PLANS
---------------------------
GET    /api/plans/                      - List available plans
GET    /api/plans/{id}/                 - Get plan detail

GET    /api/meal-subscriptions/         - List user meal subscriptions
POST   /api/meal-subscriptions/         - Create subscription
GET    /api/meal-subscriptions/current/ - Get current active subscription
GET    /api/meal-subscriptions/{id}/    - Get subscription detail
POST   /api/meal-subscriptions/{id}/select_meals/ - Select weekly meals

ORDERS & DELIVERY
-----------------
GET    /api/orders/                     - List orders (query: ?status=on_delivery)
GET    /api/orders/{id}/                - Get order detail

GET    /api/deliveries/                 - List deliveries
GET    /api/deliveries/upcoming/        - Get upcoming deliveries
GET    /api/deliveries/{id}/            - Get delivery detail

ADDRESSES
---------
GET    /api/addresses/                  - List user addresses
POST   /api/addresses/                  - Add address
GET    /api/addresses/{id}/             - Get address detail
PATCH  /api/addresses/{id}/             - Update address
DELETE /api/addresses/{id}/             - Delete address

PAYMENT & BILLING
-----------------
GET    /api/payment-methods/            - List payment methods
POST   /api/payment-methods/            - Add payment method
DELETE /api/payment-methods/{id}/       - Remove payment method

GET    /api/invoices/                   - List invoices
GET    /api/invoices/{id}/              - Get invoice detail

GET    /api/subscriptions/              - List subscriptions
POST   /api/subscriptions/              - Create subscription
GET    /api/subscriptions/{id}/         - Get subscription detail
POST   /api/subscriptions/{id}/pause/   - Pause subscription
POST   /api/subscriptions/{id}/cancel/  - Cancel subscription

LESSONS
-------
GET    /api/lessons/                    - List lessons
GET    /api/lessons/{id}/               - Get lesson detail

CHAT
----
GET    /api/chat-threads/               - List chat threads
POST   /api/chat-threads/               - Create thread
GET    /api/chat-threads/{id}/          - Get thread detail

GET    /api/chat-messages/              - List messages (query: ?thread_id=1)
POST   /api/chat-messages/              - Send message
PATCH  /api/chat-messages/{id}/read/    - Mark as read

WISHLIST
--------
GET    /api/wishlist/                   - List wishlist items
POST   /api/wishlist/                   - Add item
GET    /api/wishlist/{id}/              - Get item detail
PATCH  /api/wishlist/{id}/              - Update item
PATCH  /api/wishlist/{id}/purchase/     - Mark as purchased
DELETE /api/wishlist/{id}/              - Delete item

FILES
-----
GET    /api/files/                      - List user files (query: ?tag=diet_plan)
POST   /api/files/                      - Upload file
GET    /api/files/{id}/                 - Get file detail
DELETE /api/files/{id}/                 - Delete file

ANALYTICS
---------
GET    /api/analytics/weekly/           - Get weekly analytics (query: ?week_start=2025-10-20)
GET    /api/analytics/monthly/          - Get monthly analytics (query: ?month=2025-10)

NOTIFICATIONS
-------------
POST   /api/notifications/register-device/ - Register push notification token

COACH/ADMIN
-----------
GET    /api/coach/clients/              - List clients (query: ?status=active&checkin_status=pending)
GET    /api/coach/clients/{id}/         - Get client detail
POST   /api/coach/clients/{id}/assign-workout/ - Assign workout to client


WEBSOCKET ENDPOINTS
===================
These would be implemented separately using Django Channels:

ws://api.domain.com/ws/chat/{thread_id}/          - Real-time chat
ws://api.domain.com/ws/workout/{session_id}/      - Live workout tracking
ws://api.domain.com/ws/notifications/             - Real-time notifications
ws://api.domain.com/ws/cardio/{session_id}/       - Live cardio tracking


QUERY PARAMETERS
================
Most list endpoints support:
- limit: Number of items (default: 20, max: 100)
- offset: Pagination offset
- page: Page number
- ordering: Sort field (e.g., -created_at, name)
- search: Text search

Date filtering:
- date: Specific date (YYYY-MM-DD)
- from: Start date
- to: End date
- from_date: Alias for from
- to_date: Alias for to


RESPONSE FORMATS
================

Success Response:
{
    "data": {...} or [...]
}

Paginated Response:
{
    "count": 150,
    "next": "https://api.../endpoint/?page=2",
    "previous": null,
    "results": [...]
}

Error Response:
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input provided",
        "details": {
            "field_name": ["Error message"]
        }
    }
}


AUTHENTICATION
==============
All endpoints (except auth endpoints) require authentication.
Include token in header:
Authorization: Token <your-token-here>


PERMISSIONS
===========
- Most endpoints require IsAuthenticated
- Coach endpoints require is_staff=True
- Users can only access their own data (enforced in views)
"""