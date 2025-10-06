from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

# Existing routes
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')
router.register(r'workout-logs', UserWorkoutLogViewSet, basename='workoutlog')
router.register(r'meal-logs', UserMealLogViewSet, basename='meallog')
router.register(r'progress', ProgressViewSet, basename='progress')
router.register(r'wishlist', WishlistItemViewSet, basename='wishlist')

# New routes - Nutrition & Leads
router.register(r'nutrition', NutritionViewSet, basename='nutrition')
router.register(r'leads', LeadViewSet, basename='lead')

# Auth/OTP
router.register(r'otps', LoginOTPViewSet, basename='otp')

# Macro Planning
router.register(r'macro-plans', MacroPlanViewSet, basename='macroplan')
router.register(r'daily-macro-targets', DailyMacroTargetViewSet, basename='dailymacrotarget')

# Activity Tracking
router.register(r'water-logs', WaterLogViewSet, basename='waterlog')
router.register(r'activity-summaries', DailyActivitySummaryViewSet, basename='activitysummary')
router.register(r'heart-rate-samples', HeartRateSampleViewSet, basename='heartratesample')

# Check-ins
router.register(r'checkin-forms', CheckinFormViewSet, basename='checkinform')
router.register(r'checkin-questions', CheckinQuestionViewSet, basename='checkinquestion')
router.register(r'checkins', CheckinViewSet, basename='checkin')
router.register(r'checkin-answers', CheckinAnswerViewSet, basename='checkinanswer')
router.register(r'checkin-photos', CheckinPhotoViewSet, basename='checkinphoto')

# Food Library
router.register(r'food-brands', FoodBrandViewSet, basename='foodbrand')
router.register(r'foods', FoodViewSet, basename='food')
router.register(r'food-barcodes', FoodBarcodeViewSet, basename='foodbarcode')
router.register(r'food-portions', FoodPortionViewSet, basename='foodportion')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'recipe-ingredients', RecipeIngredientViewSet, basename='recipeingredient')
router.register(r'food-diary', FoodDiaryEntryViewSet, basename='fooddiary')

# Exercise Library
router.register(r'muscles', MuscleViewSet, basename='muscle')
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workout-exercises', WorkoutExerciseViewSet, basename='workoutexercise')
router.register(r'set-logs', SetLogViewSet, basename='setlog')

# Cardio
router.register(r'cardio-sessions', CardioSessionViewSet, basename='cardiosession')

# Address & Subscriptions
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

# Meal Subscriptions
router.register(r'meal-subscriptions', MealSubscriptionViewSet, basename='mealsubscription')
router.register(r'weekly-meal-selections', WeeklyMealSelectionViewSet, basename='weeklymealselection')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')

# Chat & Files
router.register(r'chat-threads', ChatThreadViewSet, basename='chatthread')
router.register(r'chat-messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'chat-attachments', ChatAttachmentViewSet, basename='chatattachment')
router.register(r'user-files', UserFileViewSet, basename='userfile')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]