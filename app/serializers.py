from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import User


from rest_framework import serializers
from .models import UserProfile
import re
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import date
from .models import *
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom fields to the response
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email

        return data

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            'id', 'user', 'name', 'description', 'duration', 
            'level', 'calories_burned', 'date', 'completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate that workout date isn't in the future
        if 'date' in data and data['date'] > date.today():
            raise serializers.ValidationError("Workout date cannot be in the future")
        return data
# ✅ Basic user info for nesting
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'username', 'email', 'date_of_birth', 'age', 'gender',
            'height', 'weight', 'unit_system', 'goal', 'target_weight',
            'dietary_preferences', 'activity_level', 'phone', 'source',
            'workouts', 'created_at', 'last_updated', 'bmi'
        ]
        read_only_fields = ['user_id', 'username', 'email', 'age', 'created_at', 'last_updated', 'bmi']
class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = [
            'id',
            'name',
            'description',
            'meal_type',
            'calories',
            'protein',
            'carbs',
            'fats',
            'fiber',
            'is_vegan',
            'is_vegetarian',
            'is_gluten_free',
            'is_dairy_free',
            'preparation_time',
            'difficulty',
            'image'
        ]


# ✅ User Workout Log — auto-link user, duration_actual is read-only
class UserWorkoutLogSerializer(serializers.ModelSerializer):
    duration_actual = serializers.DurationField(read_only=True)

    class Meta:
        model = UserWorkoutLog
        fields = [
            'id',
            'workout',
            'date',
            'start_time',
            'end_time',
            'completed',
            'satisfaction',
            'notes',
            'calories_burned',
            'duration_actual'
        ]
        read_only_fields = ['id', 'duration_actual']


# ✅ User Meal Log
class UserMealLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMealLog
        fields = [
            'id',
            'meal',
            'date',
            'consumed_at',
            'servings',
            'satisfaction',
            'notes'
        ]
        read_only_fields = ['id']


# ✅ Progress Log with front/side/back images & BMI
class ProgressSerializer(serializers.ModelSerializer):
    bmi = serializers.FloatField(read_only=True)

    class Meta:
        model = Progress
        fields = [
            'id',
            'date',
            'weight',
            'body_fat_percentage',
            'muscle_mass',
            'waist_circumference',
            'hip_circumference',
            'notes',
            'front_image',
            'side_image',
            'back_image',
            'bmi'
        ]
        read_only_fields = ['id', 'bmi']


# ✅ Wishlist Item
class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = [
            'id',
            'name',
            'description',
            'category',
            'priority',
            'estimated_price',
            'url',
            'added_on',
            'is_purchased',
            'purchased_on'
        ]
        read_only_fields = ['id', 'added_on']

# Add these serializers to your existing serializers.py file

# =====================================
# Nutrition
# =====================================
class NutritionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nutrition
        fields = [
            'id', 'date', 'calories_consumed', 'protein_consumed',
            'carbs_consumed', 'fats_consumed', 'fiber_consumed',
            'water_intake', 'notes'
        ]
        read_only_fields = ['id']


# =====================================
# Lead Management
# =====================================
class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'country', 'notes', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =====================================
# Auth/OTP
# =====================================
class LoginOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginOTP
        fields = [
            'id', 'channel', 'destination', 'code', 'expires_at',
            'used_at', 'attempt_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =====================================
# Macro Planning
# =====================================
class MacroPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MacroPlan
        fields = [
            'id', 'source', 'start_date', 'end_date', 'bmr', 'tdee',
            'calorie_target', 'protein_g', 'carbs_g', 'fats_g',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyMacroTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMacroTarget
        fields = [
            'id', 'date', 'calorie_target', 'protein_g', 'carbs_g',
            'fats_g', 'rollover_from_yesterday'
        ]
        read_only_fields = ['id']


# =====================================
# Activity Tracking
# =====================================
class WaterLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLog
        fields = ['id', 'date', 'amount_ml', 'created_at']
        read_only_fields = ['id', 'created_at']


class DailyActivitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivitySummary
        fields = ['id', 'date', 'steps', 'calories_burned', 'distance_m']
        read_only_fields = ['id']


class HeartRateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeartRateSample
        fields = ['id', 'ts', 'bpm']
        read_only_fields = ['id']


# =====================================
# Check-ins
# =====================================
class CheckinQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckinQuestion
        fields = ['id', 'order', 'text', 'type', 'choices']
        read_only_fields = ['id']


class CheckinFormSerializer(serializers.ModelSerializer):
    questions = CheckinQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = CheckinForm
        fields = ['id', 'name', 'active', 'questions']
        read_only_fields = ['id']


class CheckinAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = CheckinAnswer
        fields = ['id', 'question', 'question_text', 'value']
        read_only_fields = ['id', 'question_text']


class CheckinPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckinPhoto
        fields = ['id', 'kind', 'image']
        read_only_fields = ['id']


class CheckinSerializer(serializers.ModelSerializer):
    answers = CheckinAnswerSerializer(many=True, read_only=True)
    photos = CheckinPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Checkin
        fields = [
            'id', 'date', 'form', 'notes', 'sleep_hours',
            'energy_rating', 'meal_plan_use', 'workout_plan_use',
            'answers', 'photos', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =====================================
# Food Library
# =====================================
class FoodBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodBrand
        fields = ['id', 'name']
        read_only_fields = ['id']


class FoodBarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodBarcode
        fields = ['id', 'code']
        read_only_fields = ['id']


class FoodPortionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodPortion
        fields = ['id', 'name', 'unit', 'quantity', 'grams']
        read_only_fields = ['id']


class FoodSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    barcodes = FoodBarcodeSerializer(many=True, read_only=True)
    portions = FoodPortionSerializer(many=True, read_only=True)

    class Meta:
        model = Food
        fields = [
            'id', 'name', 'brand', 'brand_name', 'is_custom',
            'created_by', 'calories', 'protein', 'carbs', 'fat',
            'fiber', 'allergens', 'image', 'barcodes', 'portions'
        ]
        read_only_fields = ['id', 'brand_name', 'created_by']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'food', 'food_name', 'grams']
        read_only_fields = ['id', 'food_name']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'created_by', 'created_by_username',
            'is_public', 'image', 'ingredients'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username']


class FoodDiaryEntrySerializer(serializers.ModelSerializer):
    food_name = serializers.SerializerMethodField()

    class Meta:
        model = FoodDiaryEntry
        fields = [
            'id', 'date', 'time', 'meal_time', 'food', 'recipe',
            'meal', 'portion', 'servings', 'notes', 'food_name'
        ]
        read_only_fields = ['id']

    def get_food_name(self, obj):
        if obj.food:
            return obj.food.name
        elif obj.recipe:
            return obj.recipe.name
        elif obj.meal:
            return obj.meal.name
        return None


# =====================================
# Exercise Library
# =====================================
class MuscleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscle
        fields = ['id', 'name', 'group']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    primary_muscle_name = serializers.CharField(source='primary_muscle.name', read_only=True)
    secondary_muscle_names = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'primary_muscle', 'primary_muscle_name',
            'secondary_muscles', 'secondary_muscle_names', 'equipment',
            'video_url', 'instructions', 'unilateral', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'primary_muscle_name']

    def get_secondary_muscle_names(self, obj):
        return [m.name for m in obj.secondary_muscles.all()]


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = [
            'id', 'exercise', 'exercise_name', 'order', 'sets',
            'reps', 'reps_min', 'reps_max', 'time_seconds',
            'distance_m', 'rest_seconds', 'rpe_min', 'rpe_max',
            'tempo', 'notes'
        ]
        read_only_fields = ['id', 'exercise_name']


class SetLogSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = SetLog
        fields = [
            'id', 'session', 'exercise', 'exercise_name', 'order',
            'set_number', 'reps', 'weight_kg', 'time_seconds',
            'distance_m', 'rpe', 'completed', 'notes'
        ]
        read_only_fields = ['id', 'exercise_name']


# =====================================
# Cardio
# =====================================
class CardioSessionSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CardioSession
        fields = [
            'id', 'activity', 'started_at', 'ended_at', 'distance_m',
            'calories', 'avg_hr', 'max_hr', 'notes', 'duration',
            'created_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at']

    def get_duration(self, obj):
        duration = obj.duration
        if duration:
            return str(duration)
        return None


# =====================================
# Subscriptions & Payments
# =====================================
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'full_name', 'phone', 'line1', 'line2', 'city',
            'province', 'postal_code', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'slug', 'name', 'description', 'active']
        read_only_fields = ['id']


class PlanSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'product', 'product_name', 'name', 'interval',
            'price_amount', 'currency', 'is_default', 'sort_order'
        ]
        read_only_fields = ['id', 'product_name']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_name', 'status', 'started_at',
            'current_period_end', 'auto_renew', 'created_at'
        ]
        read_only_fields = ['id', 'plan_name', 'created_at']


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'provider', 'brand', 'last4', 'token',
            'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'subscription', 'amount', 'currency', 'due_date',
            'paid_at', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'method', 'amount', 'currency',
            'provider_id', 'succeeded', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =====================================
# Meal Subscriptions
# =====================================
class WeeklyMealSelectionSerializer(serializers.ModelSerializer):
    meal_name = serializers.CharField(source='meal.name', read_only=True)

    class Meta:
        model = WeeklyMealSelection
        fields = ['id', 'week_start', 'meal', 'meal_name', 'quantity']
        read_only_fields = ['id', 'meal_name']


class MealSubscriptionSerializer(serializers.ModelSerializer):
    address_display = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    weekly_selections = WeeklyMealSelectionSerializer(many=True, read_only=True)

    class Meta:
        model = MealSubscription
        fields = [
            'id', 'address', 'address_display', 'plan', 'plan_name',
            'meals_per_week', 'portion', 'protein_preference',
            'delivery_window', 'start_date', 'status',
            'weekly_selections', 'created_at'
        ]
        read_only_fields = ['id', 'address_display', 'plan_name', 'created_at']

    def get_address_display(self, obj):
        return f"{obj.address.full_name}, {obj.address.city}"


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'id', 'subscription', 'scheduled_date', 'delivered_at',
            'status', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =====================================
# Chat & Files
# =====================================
class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachment
        fields = ['id', 'file']
        read_only_fields = ['id']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    attachments = ChatAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'thread', 'sender', 'sender_username', 'text',
            'read_at', 'attachments', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'sender_username', 'created_at']


class ChatThreadSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    participant_usernames = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = [
            'id', 'topic', 'is_support', 'participants',
            'participant_usernames', 'messages', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_participant_usernames(self, obj):
        return [u.username for u in obj.participants.all()]


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ['id', 'name', 'file', 'tag', 'created_at']
        read_only_fields = ['id', 'created_at']
       
