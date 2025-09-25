from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from .models import (
    Workout, UserProfile, Meal, 
    UserWorkoutLog, UserMealLog, 
    Progress, WishlistItem
)

# Admin site customization
admin.site.site_header = "Fitness Tracker Administration"
admin.site.site_title = "Fitness Tracker Admin Portal"
admin.site.index_title = "Welcome to Fitness Tracker Admin"

# Unregister the default User admin
admin.site.unregister(User)

# Custom form for UserProfile with validation
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def clean_weight(self):
        weight = self.cleaned_data['weight']
        if weight <= 0:
            raise forms.ValidationError("Weight must be positive")
        return weight

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileForm
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fieldsets = (
        ('Personal Info', {
            'fields': ('date_of_birth', 'age', 'gender', 'phone')
        }),
        ('Body Measurements', {
            'fields': ('height', 'weight', 'unit_system', 'body_fat_percentage', 'bmi')
        }),
        ('Goals & Preferences', {
            'fields': ('goal', 'target_weight', 'dietary_preferences', 'activity_level')
        }),
        ('Other Info', {
            'fields': ('source',)
        }),
    )
    readonly_fields = ('age', 'bmi')

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_age', 'get_bmi', 'profile_link')
    list_select_related = ('profile',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = ['activate_users', 'deactivate_users']
    
    @admin.display(description='Age')
    def get_age(self, instance):
        return instance.profile.age if hasattr(instance, 'profile') else None
    
    @admin.display(description='BMI')
    def get_bmi(self, instance):
        return instance.profile.bmi if hasattr(instance, 'profile') else None
    
    @admin.display(description='Profile')
    def profile_link(self, instance):
        if not hasattr(instance, 'profile'):
            return "No Profile"
        url = reverse('admin:fitness_app_userprofile_change', args=[instance.profile.id])
        return format_html('<a href="{}" class="button">View Profile</a>', url)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)
    
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were activated.')
    
    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were deactivated.')

# Custom filter for workout level
class WorkoutLevelFilter(admin.SimpleListFilter):
    title = 'Workout Level'
    parameter_name = 'level'
    
    def lookups(self, request, model_admin):
        return Workout.LEVEL_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(level=self.value())
        return queryset

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'user_link', 
        'date', 
        'duration', 
        'level_badge', 
        'calories_burned', 
        'completed'  # Changed from 'completed_status' to actual field
    )
    list_filter = (WorkoutLevelFilter, 'completed', 'date', 'user')
    search_fields = ('name', 'description', 'user__username')
    date_hierarchy = 'date'
    list_per_page = 25
    list_editable = ('completed',)  # Now matches the field in list_display
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'description')
        }),
        ('Details', {
            'fields': ('date', 'duration', 'level', 'calories_burned', 'completed')
        }),
    )
    autocomplete_fields = ['user']
    
    @admin.display(description='User')
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Level')
    def level_badge(self, obj):
        colors = {
            'beginner': 'green',
            'intermediate': 'orange',
            'advanced': 'red'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 2px 6px; border-radius: 10px;">{}</span>',
            colors.get(obj.level, 'gray'),
            obj.get_level_display()
        )
    
    # Optional display method (not used in list_display)
    @admin.display(description='Status', boolean=True)
    def completed_status(self, obj):
        return obj.completed

# Custom form for Meal with validation
class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = '__all__'
    
    def clean_calories(self):
        calories = self.cleaned_data['calories']
        if calories <= 0:
            raise forms.ValidationError("Calories must be positive")
        return calories

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    form = MealForm
    list_display = (
        'name', 
        'meal_type', 
        'nutritional_summary', 
        'dietary_tags', 
        'prep_info',
        'image_preview'
    )
    list_filter = ('meal_type', 'is_vegan', 'is_vegetarian', 'is_gluten_free', 'is_dairy_free', 'difficulty')
    search_fields = ('name', 'description')
    readonly_fields = ('nutritional_info', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'meal_type', 'image', 'image_preview')
        }),
        ('Nutritional Information', {
            'fields': ('calories', 'protein', 'carbs', 'fats', 'fiber', 'nutritional_info')
        }),
        ('Dietary Information', {
            'fields': ('is_vegan', 'is_vegetarian', 'is_gluten_free', 'is_dairy_free')
        }),
        ('Preparation', {
            'fields': ('preparation_time', 'difficulty')
        }),
    )
    
    @admin.display(description='Nutritional Summary')
    def nutritional_summary(self, obj):
        return f"{obj.calories} kcal | P: {obj.protein}g | C: {obj.carbs}g | F: {obj.fats}g"
    
    @admin.display(description='Dietary Tags')
    def dietary_tags(self, obj):
        tags = []
        if obj.is_vegan:
            tags.append('Vegan')
        elif obj.is_vegetarian:
            tags.append('Vegetarian')
        if obj.is_gluten_free:
            tags.append('GF')
        if obj.is_dairy_free:
            tags.append('DF')
        return ', '.join(tags) if tags else '-'
    
    @admin.display(description='Prep Info')
    def prep_info(self, obj):
        if obj.preparation_time:
            return f"{obj.preparation_time} min | {obj.get_difficulty_display()}"
        return obj.get_difficulty_display()
    
    @admin.display(description='Nutritional Info')
    def nutritional_info(self, obj):
        return mark_safe(
            f"<table>"
            f"<tr><th>Calories:</th><td>{obj.calories}</td></tr>"
            f"<tr><th>Protein:</th><td>{obj.protein}g</td></tr>"
            f"<tr><th>Carbs:</th><td>{obj.carbs}g</td></tr>"
            f"<tr><th>Fats:</th><td>{obj.fats}g</td></tr>"
            f"<tr><th>Fiber:</th><td>{obj.fiber}g</td></tr>"
            f"</table>"
        )
    
    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "-"

# Custom filter for workout log completion
class CompletionStatusFilter(admin.SimpleListFilter):
    title = 'Completion Status'
    parameter_name = 'completed'
    
    def lookups(self, request, model_admin):
        return (
            ('completed', 'Completed Workouts'),
            ('not_completed', 'Planned Workouts'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'completed':
            return queryset.filter(completed=True)
        if self.value() == 'not_completed':
            return queryset.filter(completed=False)
        return queryset

@admin.register(UserWorkoutLog)
class UserWorkoutLogAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'workout_link',
        'date',
        'duration_display',
        'calories_burned',
        'completion_status',
        'satisfaction_stars',
        'notes_preview'
    )
    list_filter = (CompletionStatusFilter, 'date', 'user', 'workout__level')
    search_fields = ('user__username', 'workout__name', 'notes')
    date_hierarchy = 'date'
    list_per_page = 30
    fieldsets = (
        (None, {
            'fields': ('user', 'workout', 'date')
        }),
        ('Session Details', {
            'fields': ('start_time', 'end_time', 'completed', 'calories_burned')
        }),
        ('Feedback', {
            'fields': ('satisfaction', 'notes')
        }),
    )
    autocomplete_fields = ['user', 'workout']
    
    @admin.display(description='User')
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Workout')
    def workout_link(self, obj):
        url = reverse('admin:fitness_app_workout_change', args=[obj.workout.id])
        return format_html('<a href="{}">{}</a>', url, obj.workout.name)
    
    @admin.display(description='Duration')
    def duration_display(self, obj):
        if obj.duration_actual:
            hours, remainder = divmod(obj.duration_actual.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
        return "-"
    
    @admin.display(description='Completed', boolean=True)
    def completion_status(self, obj):
        return obj.completed
    
    @admin.display(description='Satisfaction')
    def satisfaction_stars(self, obj):
        if obj.satisfaction:
            return '★' * obj.satisfaction + '☆' * (5 - obj.satisfaction)
        return "-"
    
    @admin.display(description='Notes')
    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return "-"

@admin.register(UserMealLog)
class UserMealLogAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'meal_link',
        'date',
        'consumed_at',
        'servings',
        'total_nutrition',
        'satisfaction_stars',
        'notes_preview'
    )
    list_filter = ('date', 'user', 'meal__meal_type')
    search_fields = ('user__username', 'meal__name', 'notes')
    date_hierarchy = 'date'
    list_per_page = 30
    fieldsets = (
        (None, {
            'fields': ('user', 'meal', 'date', 'consumed_at', 'servings')
        }),
        ('Feedback', {
            'fields': ('satisfaction', 'notes')
        }),
    )
    autocomplete_fields = ['user', 'meal']
    
    @admin.display(description='User')
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Meal')
    def meal_link(self, obj):
        url = reverse('admin:fitness_app_meal_change', args=[obj.meal.id])
        return format_html('<a href="{}">{}</a>', url, obj.meal.name)
    
    @admin.display(description='Total Nutrition')
    def total_nutrition(self, obj):
        return (
            f"{obj.total_calories} kcal | "
            f"P: {obj.total_protein}g | "
            f"C: {round(obj.meal.carbs * obj.servings, 1)}g | "
            f"F: {round(obj.meal.fats * obj.servings, 1)}g"
        )
    
    @admin.display(description='Satisfaction')
    def satisfaction_stars(self, obj):
        if obj.satisfaction:
            return '★' * obj.satisfaction + '☆' * (5 - obj.satisfaction)
        return "-"
    
    @admin.display(description='Notes')
    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return "-"

# Custom filter for BMI status
class BMIFilter(admin.SimpleListFilter):
    title = 'BMI Status'
    parameter_name = 'bmi_status'
    
    def lookups(self, request, model_admin):
        return (
            ('underweight', 'Underweight (BMI < 18.5)'),
            ('normal', 'Normal (18.5 ≤ BMI < 25)'),
            ('overweight', 'Overweight (25 ≤ BMI < 30)'),
            ('obese', 'Obese (BMI ≥ 30)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'underweight':
            return queryset.filter(bmi__lt=18.5)
        if self.value() == 'normal':
            return queryset.filter(bmi__gte=18.5, bmi__lt=25)
        if self.value() == 'overweight':
            return queryset.filter(bmi__gte=25, bmi__lt=30)
        if self.value() == 'obese':
            return queryset.filter(bmi__gte=30)
        return queryset

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'date',
        'weight_display',
        'body_fat_display',
        'bmi_display',
        'muscle_mass_display',
        'waist_hip_ratio',
        'photos_available'
    )
    list_filter = (BMIFilter, 'date', 'user')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('bmi', 'image_previews')
    fieldsets = (
        (None, {
            'fields': ('user', 'date', 'notes')
        }),
        ('Measurements', {
            'fields': ('weight', 'body_fat_percentage', 'muscle_mass', 'bmi')
        }),
        ('Body Measurements', {
            'fields': ('waist_circumference', 'hip_circumference')
        }),
        ('Progress Photos', {
            'fields': ('front_image', 'side_image', 'back_image', 'image_previews')
        }),
    )
    autocomplete_fields = ['user']
    
    @admin.display(description='User')
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Weight')
    def weight_display(self, obj):
        unit = 'kg' if obj.user.profile.unit_system == 'metric' else 'lbs'
        return f"{obj.weight} {unit}"
    
    @admin.display(description='Body Fat')
    def body_fat_display(self, obj):
        return f"{obj.body_fat_percentage}%" if obj.body_fat_percentage else "-"
    
    @admin.display(description='BMI')
    def bmi_display(self, obj):
        if obj.bmi:
            if obj.bmi < 18.5:
                status = "Underweight"
                color = "blue"
            elif 18.5 <= obj.bmi < 25:
                status = "Normal"
                color = "green"
            elif 25 <= obj.bmi < 30:
                status = "Overweight"
                color = "orange"
            else:
                status = "Obese"
                color = "red"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color, obj.bmi, status
            )
        return "-"
    
    @admin.display(description='Muscle Mass')
    def muscle_mass_display(self, obj):
        if obj.muscle_mass:
            unit = 'kg' if obj.user.profile.unit_system == 'metric' else 'lbs'
            return f"{obj.muscle_mass} {unit}"
        return "-"
    
    @admin.display(description='W/H Ratio')
    def waist_hip_ratio(self, obj):
        if obj.waist_circumference and obj.hip_circumference:
            ratio = round(obj.waist_circumference / obj.hip_circumference, 2)
            return str(ratio)
        return "-"
    
    @admin.display(description='Photos')
    def photos_available(self, obj):
        photos = []
        if obj.front_image:
            photos.append("Front")
        if obj.side_image:
            photos.append("Side")
        if obj.back_image:
            photos.append("Back")
        return ", ".join(photos) if photos else "-"
    
    @admin.display(description='Image Previews')
    def image_previews(self, obj):
        images = []
        if obj.front_image:
            images.append(f'<div style="float: left; margin-right: 10px;"><h4>Front</h4><img src="{obj.front_image.url}" style="max-height: 200px;" /></div>')
        if obj.side_image:
            images.append(f'<div style="float: left; margin-right: 10px;"><h4>Side</h4><img src="{obj.side_image.url}" style="max-height: 200px;" /></div>')
        if obj.back_image:
            images.append(f'<div style="float: left;"><h4>Back</h4><img src="{obj.back_image.url}" style="max-height: 200px;" /></div>')
        return format_html(''.join(images)) if images else "-"

# Custom filter for wishlist items
class PurchaseStatusFilter(admin.SimpleListFilter):
    title = 'Purchase Status'
    parameter_name = 'purchased'
    
    def lookups(self, request, model_admin):
        return (
            ('purchased', 'Purchased Items'),
            ('not_purchased', 'Unpurchased Items'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'purchased':
            return queryset.filter(is_purchased=True)
        if self.value() == 'not_purchased':
            return queryset.filter(is_purchased=False)
        return queryset

    @admin.display(description='Priority')
    def priority_display(self, obj):
        colors = {
            1: 'green',
            2: 'orange',
            3: 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )
    
    @admin.display(description='Price')
    def price_display(self, obj):
        if obj.estimated_price:
            return f"${obj.estimated_price:,.2f}"
        return "-"
    
    @admin.display(description='Status')
    def purchase_status(self, obj):
        if obj.is_purchased:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Purchased on {}</span>',
                obj.purchased_on.strftime('%Y-%m-%d') if obj.purchased_on else 'unknown date'
            )
        return format_html('<span style="color: orange;">Not purchased</span>')
    
    @admin.display(description='URL')
    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">View</a>', obj.url)
        return "-"
 

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user_display',  # Changed from user_link to user_display
        'category_badge',
        'priority',
        'is_purchased',
        'price_display',
        'url_link'
    )
    list_editable = ('priority', 'is_purchased')
    list_filter = (PurchaseStatusFilter, 'category', 'priority', 'user')
    search_fields = ('name', 'description', 'user__username')
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'description', 'category')
        }),
        ('Priority & Status', {
            'fields': ('priority', 'is_purchased', 'purchased_on')
        }),
        ('Purchase Info', {
            'fields': ('estimated_price', 'url')
        }),
    )
    autocomplete_fields = ['user']
    
    @admin.display(description='User')
    def user_display(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    
    @admin.display(description='Category')
    def category_badge(self, obj):
        colors = {
            'clothes': '#FF9AA2',
            'shoes': '#FFB7B2',
            'bags': '#FFDAC1',
            'electronics': '#E2F0CB',
            'fitness': '#B5EAD7',
            'supplements': '#C7CEEA',
            'books': '#F8C8DC'
        }
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 10px;">{}</span>',
            colors.get(obj.category, '#E0E0E0'),
            obj.get_category_display()
        )
    
    @admin.display(description='Price')
    def price_display(self, obj):
        if obj.estimated_price:
            return f"${obj.estimated_price:,.2f}"
        return "-"
    
    @admin.display(description='URL')
    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">View</a>', obj.url)
        return "-"