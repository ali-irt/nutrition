from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from datetime import date, datetime


# ---------------------------
# User & Auth Serializers
# ---------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['channel', 'destination', 'code', 'expires_at']
        read_only_fields = ['code', 'expires_at']


class OTPVerifySerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=OTP.Channel.choices)
    destination = serializers.CharField()
    code = serializers.CharField(max_length=8)


# ---------------------------
# Profile Serializers
# ---------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'date_of_birth', 'age', 'gender', 'height', 'weight',
            'unit_system', 'goal', 'target_weight', 'dietary_preferences',
            'activity_level', 'phone', 'source', 'bmi', 'status',
            'checkin_status', 'last_communication', 'program_start_date',
            'workouts_per_week', 'goal_rate_lbs_per_week',
            'calorie_rollover_enabled', 'daily_step_goal',
            'daily_water_goal_ml', 'sleep_goal_hours', 'timezone',
            'onboarding_completed', 'phone_verified', 'email_verified',
            'created_at', 'last_updated'
        ]
        read_only_fields = [
            'created_at', 'last_updated', 'age', 'bmi', 'user'
        ]

    def create(self, validated_data):
        """
        Automatically link the logged-in user to the new profile.
        """
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)




class OnboardingSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=UserProfile.GENDER_CHOICES)
    height = serializers.DecimalField(max_digits=5, decimal_places=2)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2)
    unit_system = serializers.ChoiceField(choices=UnitSystem.choices)
    goal = serializers.CharField(max_length=100)
    target_weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    dietary_preferences = serializers.ChoiceField(choices=UserProfile.DIET_CHOICES, required=False)
    activity_level = serializers.ChoiceField(choices=UserProfile.ACTIVITY_LEVEL_CHOICES)
    workouts_per_week = serializers.IntegerField(min_value=0, max_value=14)
    daily_step_goal = serializers.IntegerField(default=10000)
    daily_water_goal_ml = serializers.IntegerField(default=2000)
    phone = serializers.CharField(required=False)
    source = serializers.ChoiceField(choices=UserProfile.SOURCE_CHOICES, required=False)


# ---------------------------
# Workout Serializers
# ---------------------------

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
    
    def get_secondary_muscle_names(self, obj):
        return [m.name for m in obj.secondary_muscles.all()]


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        source='exercise',
        write_only=True
    )
    
    class Meta:
        model = WorkoutExercise
        fields = [
            'id', 'exercise', 'exercise_id', 'order', 'sets', 'reps',
            'reps_min', 'reps_max', 'time_seconds', 'distance_m',
            'rest_seconds', 'rpe_min', 'rpe_max', 'tempo', 'notes'
        ]


class WorkoutSerializer(serializers.ModelSerializer):
    items = WorkoutExerciseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Workout
        fields = [
            'id', 'name', 'description', 'duration', 'level',
            'calories_burned', 'date', 'completed', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SetLogSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    
    class Meta:
        model = SetLog
        fields = [
            'id', 'exercise', 'exercise_name', 'order', 'set_number',
            'reps', 'weight_kg', 'time_seconds', 'distance_m',
            'rpe', 'completed', 'notes'
        ]


class UserWorkoutLogSerializer(serializers.ModelSerializer):
    workout_name = serializers.CharField(source='workout.name', read_only=True)
    sets = SetLogSerializer(many=True, read_only=True)
    duration_actual = serializers.ReadOnlyField()
    
    class Meta:
        model = UserWorkoutLog
        fields = [
            'id', 'workout', 'workout_name', 'date', 'start_time',
            'end_time', 'completed', 'satisfaction', 'notes',
            'calories_burned', 'duration_actual', 'sets'
        ]


class CardioSessionSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = CardioSession
        fields = [
            'id', 'activity', 'started_at', 'ended_at', 'distance_m',
            'calories', 'avg_hr', 'max_hr', 'notes', 'duration',
            'created_at'
        ]


# ---------------------------
# Nutrition Serializers
# ---------------------------

class FoodBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodBrand
        fields = ['id', 'name']


class FoodPortionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodPortion
        fields = ['id', 'name', 'unit', 'quantity', 'grams']

class FoodSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    portions = FoodPortionSerializer(many=True, read_only=True)

    class Meta:
        model = Food
        fields = [
            'id', 'name', 'brand', 'brand_name', 'is_custom',
            'calories', 'protein', 'carbs', 'fat', 'fiber',
            'allergens', 'image', 'portions', 'created_by'
        ]
        read_only_fields = ['created_by', 'is_custom']

 
class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = ['id', 'name', 'description', 'calories', 'protein', 'carbs', 'fats', 'image']


class MealBoxItemSerializer(serializers.ModelSerializer):
    meal = MealSerializer()

    class Meta:
        model = MealBoxItem
        fields = ['id', 'meal', 'quantity']


class MealBoxSerializer(serializers.ModelSerializer):
    items = MealBoxItemSerializer(many=True, read_only=True)

    class Meta:
        model = MealBox
        fields = ['id', 'name', 'description', 'duration_days', 'price', 'week_start', 'items', 'created_at', 'updated_at']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    food = FoodSerializer(read_only=True)
    food_id = serializers.PrimaryKeyRelatedField(
        queryset=Food.objects.all(),
        source='food',
        write_only=True
    )
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'food', 'food_id', 'grams']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'created_by', 'created_by_username',
            'is_public', 'image', 'ingredients'
        ]


class FoodDiaryEntrySerializer(serializers.ModelSerializer):
    food_details = FoodSerializer(source='food', read_only=True)
    recipe_details = RecipeSerializer(source='recipe', read_only=True)
    meal_details = MealSerializer(source='meal', read_only=True)
    portion_details = FoodPortionSerializer(source='portion', read_only=True)
    
    class Meta:
        model = FoodDiaryEntry
        fields = [
            'id', 'date', 'time', 'meal_time', 'food', 'food_details',
            'recipe', 'recipe_details', 'meal', 'meal_details',
            'portion', 'portion_details', 'servings', 'notes'
        ]


class UserMealLogSerializer(serializers.ModelSerializer):
    meal_details = MealSerializer(source='meal', read_only=True)
    total_calories = serializers.ReadOnlyField()
    total_protein = serializers.ReadOnlyField()
    
    class Meta:
        model = UserMealLog
        fields = [
            'id', 'meal', 'meal_details', 'date', 'consumed_at',
            'servings', 'satisfaction', 'notes', 'total_calories',
            'total_protein'
        ]


# ---------------------------
# Macro & Targets Serializers
# ---------------------------

class MacroPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MacroPlan
        fields = [
            'id', 'source', 'start_date', 'end_date', 'bmr', 'tdee',
            'calorie_target', 'protein_g', 'carbs_g', 'fats_g',
            'active', 'created_at'
        ]


class DailyMacroTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMacroTarget
        fields = [
            'id', 'date', 'calorie_target', 'protein_g', 'carbs_g',
            'fats_g', 'rollover_from_yesterday'
        ]


# ---------------------------
# Progress & Tracking Serializers
# ---------------------------

class ProgressSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    
    class Meta:
        model = Progress
        fields = [
            'id', 'date', 'weight', 'body_fat_percentage', 'muscle_mass',
            'waist_circumference', 'hip_circumference', 'notes', 'bmi',
            'front_image', 'side_image', 'back_image'
        ]


class WaterLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLog
        fields = ['id', 'date', 'amount_ml', 'created_at']


class DailyActivitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivitySummary
        fields = ['id', 'date', 'steps', 'calories_burned', 'distance_m']


class HeartRateSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeartRateSample
        fields = ['id', 'ts', 'bpm']


# ---------------------------
# Check-in Serializers
# ---------------------------

class CheckinQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckinQuestion
        fields = ['id', 'order', 'text', 'type', 'choices']


class CheckinFormSerializer(serializers.ModelSerializer):
    questions = CheckinQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = CheckinForm
        fields = ['id', 'name', 'active', 'questions']


class CheckinPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckinPhoto
        fields = ['id', 'kind', 'image']


class CheckinAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    
    class Meta:
        model = CheckinAnswer
        fields = ['id', 'question', 'question_text', 'value']


class CheckinSerializer(serializers.ModelSerializer):
    photos = CheckinPhotoSerializer(many=True, read_only=True)
    answers = CheckinAnswerSerializer(many=True, read_only=True)
    form_name = serializers.CharField(source='form.name', read_only=True)
    
    class Meta:
        model = Checkin
        fields = [
            'id', 'date', 'form', 'form_name', 'notes', 'sleep_hours',
            'energy_rating', 'meal_plan_use', 'workout_plan_use',
            'photos', 'answers', 'created_at'
        ]


# ---------------------------
# Subscription & Payment Serializers
# ---------------------------

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'full_name', 'phone', 'line1', 'line2', 'city',
            'province', 'postal_code', 'is_default', 'created_at'
        ]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'slug', 'name', 'description', 'active']


class PlanSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'product', 'product_name', 'name', 'interval',
            'price_amount', 'currency', 'is_default', 'sort_order'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_details', 'status', 'started_at',
            'current_period_end', 'auto_renew', 'created_at'
        ]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'provider', 'brand', 'last4', 'is_default', 'created_at'
        ]
        read_only_fields = ['token']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'subscription', 'amount', 'currency', 'due_date',
            'paid_at', 'status', 'created_at'
        ]


# ---------------------------
# Meal Subscription Serializers
# ---------------------------

class MealPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlan
        fields = ['id', 'name', 'plan_type', 'price', 'calories_per_day']


class WeeklyMealSelectionSerializer(serializers.ModelSerializer):
    meal_details = MealSerializer(source='meal', read_only=True)
    
    class Meta:
        model = WeeklyMealSelection
        fields = ['id', 'week_start', 'meal', 'meal_details', 'quantity']


class MealSubscriptionSerializer(serializers.ModelSerializer):
    address_details = AddressSerializer(source='address', read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)
    weekly_selections = WeeklyMealSelectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MealSubscription
        fields = [
            'id', 'address', 'address_details', 'plan', 'plan_details',
            'meals_per_week', 'portion', 'protein_preference',
            'delivery_window', 'start_date', 'status',
            'weekly_selections', 'created_at'
        ]


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'id', 'subscription', 'scheduled_date', 'delivered_at',
            'status', 'notes', 'created_at'
        ]


class MealOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealOrderItem
        fields = ['id', 'name', 'quantity', 'day']


class MealOrderSerializer(serializers.ModelSerializer):
    items = MealOrderItemSerializer(many=True, read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = MealOrder
        fields = [
            'id', 'customer', 'customer_name', 'plan', 'plan_name',
            'order_no', 'status', 'shipping_name', 'shipping_address',
            'items_count', 'total_price', 'scheduled_date',
            'delivered_at', 'created_at', 'items'
        ]


# ---------------------------
# Chat Serializers
# ---------------------------

class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachment
        fields = ['id', 'file']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    receiver_name = serializers.CharField(source='reciever.get_full_name', read_only=True)
    attachments = ChatAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'thread', 'sender', 'sender_name', 'reciever',
            'receiver_name', 'text', 'read_at', 'attachments',
            'created_at'
        ]


class ChatThreadSerializer(serializers.ModelSerializer):
    participants_details = UserSerializer(source='participants', many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatThread
        fields = [
            'id', 'participants', 'participants_details', 'topic',
            'is_support', 'last_message', 'unread_count', 'created_at'
        ]
    
    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return ChatMessageSerializer(last).data if last else None
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.messages.filter(reciever=user, read_at__isnull=True).count()

    
# ---------------------------
# Dashboard & Summary Serializers
# ---------------------------

class DashboardSummarySerializer(serializers.Serializer):
    today = serializers.DateField()
    calories_consumed = serializers.IntegerField()
    calories_target = serializers.IntegerField()
    protein_consumed = serializers.FloatField()
    protein_target = serializers.IntegerField()
    carbs_consumed = serializers.FloatField()
    carbs_target = serializers.IntegerField()
    fats_consumed = serializers.FloatField()
    fats_target = serializers.IntegerField()
    water_consumed_ml = serializers.IntegerField()
    water_goal_ml = serializers.IntegerField()
    steps = serializers.IntegerField()
    steps_goal = serializers.IntegerField()
    workouts_completed = serializers.IntegerField()
    workouts_scheduled = serializers.IntegerField()
    current_weight = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    target_weight = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    weight_change_this_week = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)


class WeeklySummarySerializer(serializers.Serializer):
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    avg_calories = serializers.FloatField()
    total_workouts = serializers.IntegerField()
    avg_steps = serializers.IntegerField()
    weight_change = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'video_url', 'created_at', 'updated_at']


class WishlistSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.PrimaryKeyRelatedField(
        queryset=Lesson.objects.all(),
        source='lesson',
        write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ['id', 'user', 'lesson', 'lesson_id', 'added_at']
        read_only_fields = ['user', 'added_at']


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ['id', 'user', 'file', 'description', 'uploaded_at']
        read_only_fields = ['user', 'uploaded_at']
