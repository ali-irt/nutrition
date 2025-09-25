from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import User


from rest_framework import serializers
from .models import UserProfile
import re
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import date
from .models import (
    Workout,
    UserProfile,
    Meal,
    UserWorkoutLog,
    UserMealLog,
    Progress,
    WishlistItem
)

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
