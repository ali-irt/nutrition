from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, date
from django.core.validators import MinValueValidator, MaxValueValidator


class Workout(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')  # Added user relationship
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.DurationField(help_text="Duration in HH:MM:SS")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    calories_burned = models.PositiveIntegerField()
    date = models.DateField()  # Added date field
    completed = models.BooleanField(default=False)  # Added completion status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'name']
        unique_together = ['user', 'name', 'date']  # Prevent duplicate workouts

    def __str__(self):
        return f"{self.user.username}'s {self.name} on {self.date}"

class UserProfile(models.Model):
    SOURCE_CHOICES = [
        ('social', 'Social Media'),
        ('friend', 'Friend or Family'),
        ('google', 'Google Search'),
        ('ads', 'Ads'),
        ('other', 'Other'),
    ]
    
    DIET_CHOICES = [
        ('meat', 'Meat'),
        ('meat_veg', 'Meat & Veg'),
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
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
        primary_key=True  # 👈 this makes it the PK
    )
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(editable=False)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Height in cm or inches"
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Weight in kg or lbs"
    )
    unit_system = models.CharField(
        max_length=10,
        choices=[
            ('imperial', 'Imperial (lbs/in)'),
            ('metric', 'Metric (kg/cm)'),
        ],
        default='metric'
    )
    goal = models.CharField(
        max_length=100,
        help_text="e.g., Lose weight, Gain muscle"
    )
    target_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    dietary_preferences = models.CharField(
        max_length=20,
        choices=DIET_CHOICES,
        blank=True
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES,
        default='moderate'
    )
    phone = models.CharField(max_length=15, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    workouts = models.ManyToManyField(
        Workout,
        blank=True,
        related_name='users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        today = date.today()
        self.age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )
        super().save(*args, **kwargs)

    @property
    def bmi(self):
        if self.unit_system == 'imperial':
            # Convert imperial to metric for calculation
            weight_kg = self.weight * 0.453592
            height_m = self.height * 0.0254
        else:
            weight_kg = self.weight
            height_m = self.height / 100
        
        if height_m == 0:
            return 0
        return round(weight_kg / (height_m ** 2), 1)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    calories = models.PositiveIntegerField()
    protein = models.FloatField(help_text="Protein in grams")
    carbs = models.FloatField(help_text="Carbs in grams")
    fats = models.FloatField(help_text="Fats in grams")
    fiber = models.FloatField(
        help_text="Fiber in grams",
        default=0
    )
    is_vegan = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    preparation_time = models.PositiveIntegerField(
        help_text="Preparation time in minutes",
        null=True,
        blank=True
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    image = models.ImageField(
        upload_to='meal_images/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['meal_type', 'name']
        verbose_name = "Meal"
        verbose_name_plural = "Meals"

    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.name}"


class UserWorkoutLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workout_logs'
    )
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE
    )
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


class UserMealLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='meal_logs'
    )
    meal = models.ForeignKey(
        Meal,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    consumed_at = models.TimeField()
    servings = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1)]
    )
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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_entries'
    )
    date = models.DateField()
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Weight in kg or lbs"
    )
    body_fat_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )
    muscle_mass = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Muscle mass in kg or lbs"
    )
    waist_circumference = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Waist circumference in cm or inches"
    )
    hip_circumference = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hip circumference in cm or inches"
    )
    notes = models.TextField(blank=True)
    front_image = models.ImageField(
        upload_to='progress_images/',
        null=True,
        blank=True
    )
    side_image = models.ImageField(
        upload_to='progress_images/',
        null=True,
        blank=True
    )
    back_image = models.ImageField(
        upload_to='progress_images/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Progress Entry"
        verbose_name_plural = "Progress Entries"
        unique_together = ['user', 'date']

    @property
    def bmi(self):
        profile = self.user.profile
        if profile.unit_system == 'imperial':
            # Convert imperial to metric for calculation
            weight_kg = self.weight * 0.453592
            height_m = profile.height * 0.0254
        else:
            weight_kg = self.weight
            height_m = profile.height / 100
        
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

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=2
    )
    estimated_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Link to product page"
    )
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