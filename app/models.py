from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models import Sum 
from decimal import Decimal
# Shared helpers and enums
# ---------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UnitSystem(models.TextChoices):
    METRIC = "metric", "Metric (kg/cm)"
    IMPERIAL = "imperial", "Imperial (lbs/in)"


class ActivityLevel(models.TextChoices):
    SEDENTARY = "sedentary", "Sedentary"
    LIGHT = "light", "Lightly Active"
    MODERATE = "moderate", "Moderately Active"
    ACTIVE = "active", "Very Active"
    EXTREME = "extreme", "Extremely Active"


class MealTime(models.TextChoices):
    BREAKFAST = "breakfast", "Breakfast"
    LUNCH = "lunch", "Lunch"
    DINNER = "dinner", "Dinner"
    SNACK = "snack", "Snack"


class ServingUnit(models.TextChoices):
    GRAM = "g", "Gram"
    ML = "ml", "Milliliter"
    PIECE = "piece", "Piece"
    CUP = "cup", "Cup"
    TBSP = "tbsp", "Tablespoon"
    TSP = "tsp", "Teaspoon"
    OZ = "oz", "Ounce"
    PLATE = "plate", "Plate"


# ---------------------------
# EXISTING MODELS (kept names)
# ---------------------------

class Workout(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.DurationField(help_text="Duration in HH:MM:SS")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    calories_burned = models.PositiveIntegerField()
    date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'name']
        unique_together = ['user', 'name', 'date']

    def __str__(self):
        return f"{self.user.username}'s {self.name} on {self.date}"


class UserProfile(models.Model):
    SOURCE_CHOICES = [
        ('social', 'Social Media'),
        ('friend', 'Friend or Family'),
        ('google', 'Google Search'),
        ('ads', 'Ads'),
        ('other', 'Other'),
        # Added to match onboarding screens
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tv', 'TV'),
    ]

    DIET_CHOICES = [
        ('meat', 'Meat'),
        ('meat_veg', 'Meat & Veg'),
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('other', 'Other'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('light', 'Lightly Active'),
        ('moderate', 'Moderately Active'),
        ('active', 'Very Active'),
        ('extreme', 'Extremely Active'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(editable=False, null=True, blank=True)
    gender = models.CharField(max_length=20,null=True, choices=GENDER_CHOICES)
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm or inches", null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2,null=True, help_text="Weight in kg or lbs")
    unit_system = models.CharField(
        max_length=10,
        choices=UnitSystem.choices,
        default=UnitSystem.METRIC
    )
    goal = models.CharField(max_length=100, help_text="e.g., Lose weight, Gain muscle")
    target_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dietary_preferences = models.CharField(max_length=20, choices=DIET_CHOICES, blank=True)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, default='moderate' )
    phone = models.CharField(max_length=20, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    plan = models.CharField(max_length=100, blank=True)
    dietition_assigned = models.CharField(max_length=100, blank=True)
    progress = models.IntegerField(blank=True, null=True, help_text="Progress percentage towards goal")
    workouts = models.ManyToManyField(Workout, blank=True, related_name='users')

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Client management fields (kept)
    status = models.CharField(max_length=20, default='active', choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('payment_error', 'Payment Error'),
        ('inactive', 'Inactive'),
    ])
    checkin_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ])
    last_communication = models.DateTimeField(null=True, blank=True)
    program_start_date = models.DateField(null=True, blank=True)
    payment_error = models.BooleanField(default=False)

    # New onboarding + goals
    workouts_per_week = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(14)])
    goal_rate_lbs_per_week = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    calorie_rollover_enabled = models.BooleanField(default=False)
    daily_step_goal = models.PositiveIntegerField(default=10000)
    daily_water_goal_ml = models.PositiveIntegerField(default=2000)
    sleep_goal_hours = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    onboarding_completed = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    
    @property
    def bmi(self):
        if self.unit_system == UnitSystem.IMPERIAL:
            weight_kg = float(self.weight) * 0.453592
            height_m = float(self.height) * 0.0254
        else:
            weight_kg = float(self.weight)
            height_m = float(self.height) / 100
        if height_m == 0:
            return 0
        return round(weight_kg / (height_m ** 2), 1)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


# models.py
from django.db import models

class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    calories = models.PositiveIntegerField(help_text="Calories per serving")
    protein = models.FloatField(help_text="Protein (g)")
    carbs = models.FloatField(help_text="Carbohydrates (g)")
    fats = models.FloatField(help_text="Fats (g)")
    fiber = models.FloatField(default=0, help_text="Fiber (g)")
    
    # Dietary flags
    is_vegan = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)

    # Extras
    preparation_time = models.PositiveIntegerField(null=True, blank=True, help_text="Preparation time (minutes)")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    image = models.ImageField(upload_to='meal_images/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['meal_type', 'name']
        verbose_name = "Meal"
        verbose_name_plural = "Meals"

    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.name}"

    @property
    def macros_ratio(self):
        total = self.protein + self.carbs + self.fats
        if total == 0:
            return {"protein": 0, "carbs": 0, "fats": 0}
        return {
            "protein": round((self.protein / total) * 100, 1),
            "carbs": round((self.carbs / total) * 100, 1),
            "fats": round((self.fats / total) * 100, 1),

        }

class MealBoxItem(models.Model):
    meal_box = models.ForeignKey('MealBox', on_delete=models.CASCADE, related_name='items')
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class MealBox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meal_boxes")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration_days = models.IntegerField(default=7)
    price = models.DecimalField(max_digits=8, null=True, blank=True, decimal_places=2)
    week_start = models.DateField(default=timezone.now().date())
    meals = models.ManyToManyField('Meal', through='MealBoxItem')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserWorkoutLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_logs')
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    satisfaction = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text="Rating from 1-5"
    )
    notes = models.TextField(blank=True)
    calories_burned = models.PositiveIntegerField(null=True, blank=True)

    @property
    def duration_actual(self):
        if self.start_time and self.end_time:
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            return end - start
        return None

    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = "Workout Log"
        verbose_name_plural = "Workout Logs"
        unique_together = ['user', 'workout', 'date']

    def __str__(self):
        status = "Completed" if self.completed else "Planned"
        return f"{self.user.username} - {self.workout.name} ({self.date}) - {status}"
# models.py
from django.db import models

class Nutrition(models.Model):
    KIND_CHOICES = (("ingredient", "Ingredient"), ("recipe", "Recipe"))
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="ingredient")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    meal_type = models.CharField(max_length=50, blank=True)  # breakfast/lunch/dinner/snack
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fats = models.FloatField(default=0)
    calories = models.IntegerField(default=0)
    preparation_time = models.PositiveIntegerField(null=True, blank=True)
    cooking_time = models.PositiveIntegerField(null=True, blank=True)
    instructions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

class NutritionTemplate(models.Model):
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=50, blank=True)
    meals_per_day = models.PositiveIntegerField(null=True, blank=True)
    target_calories = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
class UserMealLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_logs')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    date = models.DateField()
    consumed_at = models.TimeField()
    servings = models.FloatField(default=1.0, validators=[MinValueValidator(0.1)])
    satisfaction = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text="Rating from 1-5"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-consumed_at']
        verbose_name = "Meal Log"
        verbose_name_plural = "Meal Logs"

    @property
    def total_calories(self):
        return round(self.meal.calories * self.servings)

    @property
    def total_protein(self):
        return round(self.meal.protein * self.servings, 1)

    def __str__(self):
        return f"{self.user.username} - {self.meal.name} x{self.servings} ({self.date})"


class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_entries')
    date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg or lbs")
    body_fat_percentage = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    muscle_mass = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Muscle mass in kg or lbs")
    waist_circumference = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Waist circumference in cm or inches")
    hip_circumference = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Hip circumference in cm or inches")
    notes = models.TextField(blank=True)
    front_image = models.ImageField(upload_to='progress_images/', null=True, blank=True)
    side_image = models.ImageField(upload_to='progress_images/', null=True, blank=True)
    back_image = models.ImageField(upload_to='progress_images/', null=True, blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Progress Entry"
        verbose_name_plural = "Progress Entries"
        unique_together = ['user', 'date']

    @property
    def bmi(self):
        profile = self.user.profile
        if profile.unit_system == UnitSystem.IMPERIAL:
            weight_kg = float(self.weight) * 0.453592
            height_m = float(profile.height) * 0.0254
        else:
            weight_kg = float(self.weight)
            height_m = float(profile.height) / 100
        if height_m == 0:
            return 0
        return round(weight_kg / (height_m ** 2), 1)

    def __str__(self):
        return f"{self.user.username} - {self.weight} on {self.date}"


class WishlistItem(models.Model):
    CATEGORY_CHOICES = [
        ('clothes', 'Clothes'),
        ('shoes', 'Shoes'),
        ('bags', 'Bags'),
        ('electronics', 'Electronics'),
        ('fitness', 'Fitness Equipment'),
        ('supplements', 'Supplements'),
        ('books', 'Books'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=2)
    estimated_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    url = models.URLField(max_length=500, blank=True, help_text="Link to product page")
    added_on = models.DateTimeField(auto_now_add=True)
    is_purchased = models.BooleanField(default=False)
    purchased_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', '-added_on']
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        purchased = " (Purchased)" if self.is_purchased else ""
        return f"{self.user.username}'s Wishlist: {self.name}{purchased}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ("New", "New"),
        ("Contacted", "Contacted"),
        ("In Dialogue", "In Dialogue"),
        ("On Hold", "On Hold"),
        ("Won", "Won"),
        ("Lost", "Lost"),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default="New")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.status}"


# ---------------------------
# NEW: Auth/OTP verification
# ---------------------------

class OTP(TimeStampedModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    channel = models.CharField(max_length=10, choices=Channel.choices)
    destination = models.CharField(max_length=255)  # email or E.164 phone
    code = models.CharField(max_length=8)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)

    def is_valid(self) -> bool:
        return self.used_at is None and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.channel} to {self.destination}"


# ---------------------------
# NEW: Macro plans and daily targets
# ---------------------------

class MacroPlan(TimeStampedModel):
    SOURCE_CHOICES = [('auto', 'Auto'), ('manual', 'Manual')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="macro_plans")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='auto')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    bmr = models.PositiveIntegerField(null=True, blank=True)
    tdee = models.PositiveIntegerField(null=True, blank=True)
    calorie_target = models.PositiveIntegerField()

    protein_g = models.PositiveIntegerField()
    carbs_g = models.PositiveIntegerField()
    fats_g = models.PositiveIntegerField()

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.user.username} MacroPlan {self.start_date}"


class DailyMacroTarget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_macro_targets")
    date = models.DateField()
    calorie_target = models.PositiveIntegerField()
    protein_g = models.PositiveIntegerField()
    carbs_g = models.PositiveIntegerField()
    fats_g = models.PositiveIntegerField()
    rollover_from_yesterday = models.IntegerField(default=0)  # +/- kcal

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} targets for {self.date}"


# ---------------------------
# NEW: Water, steps, HR
# ---------------------------

class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="water_logs")
    date = models.DateField(default=timezone.now)
    amount_ml = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.user.username} {self.amount_ml} ml on {self.date}"


class DailyActivitySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_summaries")
    date = models.DateField()
    steps = models.PositiveIntegerField(default=0)
    calories_burned = models.PositiveIntegerField(default=0)
    distance_m = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} activity {self.date}"


class HeartRateSample(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hr_samples")
    ts = models.DateTimeField()
    bpm = models.PositiveSmallIntegerField()

    class Meta:
        indexes = [models.Index(fields=["user", "ts"])]

    def __str__(self):
        return f"{self.user.username} {self.bpm} bpm @ {self.ts}"


# ---------------------------
# NEW: Check-ins with photos
# ---------------------------

class CheckinForm(models.Model):
    name = models.CharField(max_length=120, default="Weekly Check-in")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CheckinQuestion(models.Model):
    class Type(models.TextChoices):
        RATING = "rating", "Rating (1-5)"
        NUMBER = "number", "Number"
        TEXT = "text", "Text"
        CHOICE = "choice", "Single Choice"

    form = models.ForeignKey(CheckinForm, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField(default=1)
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=16, choices=Type.choices, default=Type.TEXT)
    choices = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class Checkin(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="checkins")
    date = models.DateField(default=timezone.now)
    form = models.ForeignKey(CheckinForm, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    sleep_hours = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    energy_rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    meal_plan_use = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    workout_plan_use = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} check-in {self.date}"


class CheckinAnswer(models.Model):
    checkin = models.ForeignKey(Checkin, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(CheckinQuestion, on_delete=models.CASCADE)
    value = models.TextField(blank=True)


class CheckinPhoto(models.Model):
    checkin = models.ForeignKey(Checkin, on_delete=models.CASCADE, related_name="photos")
    kind = models.CharField(max_length=10, choices=[("front","Front"),("side","Side"),("back","Back")])
    image = models.ImageField(upload_to="checkin_photos/")


# ---------------------------
# NEW: Food library + diary
# ---------------------------

class FoodBrand(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Food(models.Model):
    food_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(FoodBrand, on_delete=models.SET_NULL, null=True, blank=True)
    is_custom = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # nutrition per 100g
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    fiber = models.FloatField(default=0)

    allergens = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="food_images/", null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class FoodBarcode(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="barcodes")
    code = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.code


class FoodPortion(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="portions")
    name = models.CharField(max_length=64, default="100 g")
    unit = models.CharField(max_length=16, choices=ServingUnit.choices, default=ServingUnit.GRAM)
    quantity = models.FloatField(default=100.0)  # unit amount (e.g., 100 g)
    grams = models.FloatField()                  # how many grams this portion equals

    def __str__(self):
        return f"{self.food.name} - {self.name}"


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    is_public = models.BooleanField(default=False)
    image = models.ImageField(upload_to="recipe_images/", null=True, blank=True)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    food = models.ForeignKey(Food, on_delete=models.PROTECT)
    grams = models.FloatField()


class FoodDiaryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="food_diary_entries")
    date = models.DateField(default=timezone.now)
    time = models.TimeField(null=True, blank=True)
    meal_time = models.CharField(max_length=20, choices=MealTime.choices, default=MealTime.LUNCH)

    # one-of these can be filled
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, null=True, blank=True)  # reuse curated meals

    portion = models.ForeignKey(FoodPortion, on_delete=models.SET_NULL, null=True, blank=True)
    servings = models.FloatField(default=1.0, validators=[MinValueValidator(0.01)])

    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        label = self.food.name if self.food else (self.recipe.name if self.recipe else (self.meal.name if self.meal else "Item"))
        return f"{self.user.username} - {label} ({self.date})"


# ---------------------------
# NEW: Exercise library + per-set logs
# ---------------------------

class MuscleGroup(models.TextChoices):
    CHEST = "chest", "Chest"
    BACK = "back", "Back"
    SHOULDERS = "shoulders", "Shoulders"
    ARMS = "arms", "Arms"
    CORE = "core", "Core"
    LEGS = "legs", "Legs"
    FULL_BODY = "full_body", "Full Body"


class Muscle(models.Model):
    name = models.CharField(max_length=64, unique=True)
    group = models.CharField(max_length=20, choices=MuscleGroup.choices)

    class Meta:
        ordering = ["group", "name"]

    def __str__(self):
        return self.name


class Exercise(TimeStampedModel):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,default='admin', blank=True, related_name="created_exercises")
    name = models.CharField(max_length=120, unique=True)
    primary_muscle = models.ForeignKey(Muscle, on_delete=models.SET_NULL, null=True, related_name="primary_exercises")
    secondary_muscles = models.ManyToManyField(Muscle, blank=True, related_name="secondary_exercises")
    equipment = models.CharField(max_length=64, blank=True)
    video_url = models.URLField(blank=True)
    instructions = models.TextField(blank=True)
    unilateral = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=1)

    # prescription
    sets = models.PositiveSmallIntegerField(default=3)
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    reps_min = models.PositiveSmallIntegerField(null=True, blank=True)
    reps_max = models.PositiveSmallIntegerField(null=True, blank=True)
    time_seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    rpe_min = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    rpe_max = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    tempo = models.CharField(max_length=16, blank=True, help_text="e.g., 3-1-1-0")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = [("workout", "order")]

    def __str__(self):
        return f"{self.workout.name} - {self.exercise.name} ({self.order})"


class SetLog(models.Model):
    session = models.ForeignKey(UserWorkoutLog, on_delete=models.CASCADE, related_name="sets")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=1)         # exercise order within workout
    set_number = models.PositiveSmallIntegerField(default=1)    # set number within exercise
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    time_seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(null=True, blank=True)
    rpe = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    completed = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["session", "order", "set_number"]
        indexes = [models.Index(fields=["session", "exercise"])]

    def __str__(self):
        return f"{self.session_id} - {self.exercise.name} set {self.set_number}"


# ---------------------------
# NEW: Cardio sessions (run/walk/cycle)
# ---------------------------

class ActivityType(models.TextChoices):
    RUN = "run", "Running"
    WALK = "walk", "Walking"
    CYCLE = "cycle", "Cycling"
    OTHER = "other", "Other"


class CardioSession(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cardio_sessions")
    activity = models.CharField(max_length=16, choices=ActivityType.choices, default=ActivityType.RUN)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    distance_m = models.PositiveIntegerField(default=0)
    calories = models.PositiveIntegerField(default=0)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    @property
    def duration(self):
        if self.ended_at:
            return self.ended_at - self.started_at
        return None

    def __str__(self):
        return f"{self.user.username} {self.activity} @ {self.started_at.date()}"


# ---------------------------
# NEW: Subscriptions, checkout, delivery
# ---------------------------

class Address(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}"


class Product(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Plan(models.Model):
    INTERVAL_CHOICES = [
        ("one_time", "One time"),
        ("monthly", "Monthly"),
        ("3_month", "3 - Month"),
        ("6_month", "6 - Month"),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=150)
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="PKR")
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Subscription(TimeStampedModel):
    STATUS = [
        ("active", "Active"),
        ("trialing", "Trialing"),
        ("past_due", "Past Due"),
        ("paused", "Paused"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    started_at = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"


class PaymentMethod(TimeStampedModel):
    PROVIDER = [("card", "Card"), ("bank", "Bank Transfer"), ("gpay", "Google Pay")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_methods")
    provider = models.CharField(max_length=20, choices=PROVIDER)
    brand = models.CharField(max_length=30, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    token = models.CharField(max_length=255, blank=True)  # provider reference
    is_default = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} {self.provider} ****{self.last4}"


class Invoice(TimeStampedModel):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    order = models.OneToOneField('Order', on_delete=models.CASCADE, null=True, blank=True, related_name='order_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="PKR")
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice #{self.id} - {self.user.username}"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="payment", null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.user.username} ({self.status})"

class MealPortionChoice(models.TextChoices):
    STANDARD = "standard", "Standard"
    LOW_CAL = "low_cal", "Low Calorie"
    HIGH_PROTEIN = "high_protein", "High Protein"


class ProteinPreference(models.TextChoices):
    MEAT_AND_VEGAN = "meat_vegan", "Meat & Vegan"
    MEAT_ONLY = "meat_only", "Meat Only"
    VEGAN_ONLY = "vegan_only", "Vegan Only"

class MealPlan(models.Model):
    PLAN_TYPES = (
        ("standard", "Standard"),
        ("vegan", "Vegan"),
        ("keto", "Keto"),
        ("custom", "Custom"),
    )
    name = models.CharField(max_length=120)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default="standard")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    calories_per_day = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class MealSubscription(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meal_subscriptions")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="meal_subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)  # should point to a meal product plan
    meals_per_week = models.PositiveSmallIntegerField(default=10)  # 6/8/10/12/15/18
    portion = models.CharField(max_length=20, choices=MealPortionChoice.choices, default=MealPortionChoice.STANDARD)
    protein_preference = models.CharField(max_length=20, choices=ProteinPreference.choices, default=ProteinPreference.MEAT_AND_VEGAN)
    delivery_window = models.CharField(max_length=50, default="08:00-09:00")
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=[("active","Active"),("paused","Paused"),("canceled","Canceled")], default="active")

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} meals"


class WeeklyMealSelection(models.Model):
    subscription = models.ForeignKey(MealSubscription, on_delete=models.CASCADE, related_name="weekly_selections")
    week_start = models.DateField()  # Monday of the week
    meal = models.ForeignKey(Meal, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ["subscription", "week_start", "meal"]

    def __str__(self):
        return f"{self.subscription_id} - {self.meal.name} x{self.quantity} ({self.week_start})"


class Delivery(TimeStampedModel):
    subscription = models.ForeignKey(MealSubscription, on_delete=models.CASCADE, related_name="deliveries")
    scheduled_date = models.DateField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("scheduled","Scheduled"),("out_for_delivery","Out for Delivery"),("delivered","Delivered"),("missed","Missed")],
        default="scheduled"
    )
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Delivery {self.subscription_id} on {self.scheduled_date} - {self.status}"


# ---------------------------
# NEW: Chat and Files
# ---------------------------

class ChatThread(TimeStampedModel):
    participants = models.ManyToManyField(User, related_name="chat_threads")
    topic = models.CharField(max_length=120, blank=True)
    is_support = models.BooleanField(default=False)

    def __str__(self):
        return self.topic or f"Thread {self.id}"


class ChatMessage(TimeStampedModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    reciever = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    text = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Msg {self.id} in Thread {self.thread_id}"


class ChatAttachment(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="chat_attachments/")


class UserFile(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="user_files/")
    tag = models.CharField(max_length=50, blank=True)  # e.g., "diet plan", "report"

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField(max_length=100)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

class Inventory(models.Model):
    ingredient_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=20)
    low_stock_alert = models.PositiveIntegerField(default=10)
    reorder_level = models.FloatField(default=10)
    supplier = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def is_low_stock(self):
        return self.quantity <= self.low_stock_alert

    def __str__(self):
        return self.ingredient_name
class File(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class LessonFile(models.Model):
    file = models.FileField(upload_to="lesson_files/")
    name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.file.name

class Lesson(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    video = models.FileField(upload_to='lesson_videos/', blank=True, null=True)
    image = models.ImageField(upload_to='lesson_images/', blank=True, null=True)
    files = models.ManyToManyField(LessonFile, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class MealOrder(models.Model):
    """Complete order with payment tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping details
    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_province = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    
    # Payment details


    payment_method = models.CharField(max_length=20, choices=[
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('google_pay', 'Google Pay'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ])
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Simple mock order number generation
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{self.user.id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"

class MealOrderItem(TimeStampedModel):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    meal = models.ForeignKey(Meal, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.meal.name} x{self.quantity}"

 

class Cart(TimeStampedModel):
    """Shopping cart for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    
    def __str__(self):
        return f"{self.user.username}'s Cart"
    
    @property
    def total_items(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def subtotal(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.meal.price * item.quantity
        return total


class CartItem(TimeStampedModel):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['cart', 'meal']
    
    def __str__(self):
        return f"{self.meal.name} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.meal.price * self.quantity

