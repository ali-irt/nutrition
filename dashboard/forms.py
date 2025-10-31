from django import forms
from app.models import *
from django.forms import inlineformset_factory
from django.utils.timezone import localdate

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["first_name", "last_name", "email", "phone", "country", "notes", "status"]

class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = [
            "user", "name", "description", "duration", "level",
            "calories_burned", "date", "completed",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateInput(attrs={"type": "date", "value": localdate()}),
        }

WorkoutExerciseFormSet = inlineformset_factory(
    parent_model=Workout,
    model=WorkoutExercise,
    fields=[
        "order", "exercise", "sets", "reps", "reps_min", "reps_max",
        "time_seconds", "distance_m", "rest_seconds", "rpe_min", "rpe_max",
        "tempo", "notes",
    ],
    extra=2,
    can_delete=True,
)
class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['title', 'description', 'file', 'video']

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            allowed_types = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
            if video.content_type not in allowed_types:
                raise forms.ValidationError("Please upload a valid video file (MP4, MOV, AVI, or MPEG).")
        return video

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class LessonForm(forms.ModelForm):
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(),  # <- not ClearableFileInput with attrs
        help_text="Upload additional files (optional)",
    )
    class Meta:
        model = Lesson
        fields = ["title", "subtitle", "message", "video", "image", "files"]
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Nutrition
        fields = ["name", "description", "protein", "carbs", "fats", "calories"]
    # enforce kind in the view

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Nutrition
        fields = [
            "name", "description", "meal_type",
            "protein", "carbs", "fats", "calories",
            "preparation_time", "cooking_time", "instructions",
        ]

    def clean(self):
        cleaned = super().clean()
        # Optional: basic non-negative guard
        for f in ["protein", "carbs", "fats", "calories", "preparation_time", "cooking_time"]:
            v = cleaned.get(f)
            if v is not None and float(v) < 0:
                self.add_error(f, "Must be zero or greater.")
        return cleaned
class NutritionTemplateForm(forms.ModelForm):
    class Meta:
        model = NutritionTemplate
        fields = ["name", "language", "meals_per_day", "target_calories"]

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = [
            'ingredient_name',
            'quantity',
            'unit',
            'low_stock_alert',
            'reorder_level',
            'supplier',
            'price',
        ]
        widgets = {
            'ingredient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingredient name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. kg, L'}),
            'low_stock_alert': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
   
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name']
        widgets = {
             'username': forms.TextInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'Username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'First Name'
            }),
           
        }
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'goal',
            'plan',
            'start_date',
            'end_date',
            'status',
            'dietition_assigned',
            'progress',
        ]
        widgets = {
            'goal': forms.TextInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'Goal e.g., Muscle Build'
            }),
            'plan': forms.TextInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'Plan Type'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-pill mb-2'
            }),
            'dietition_assigned': forms.TextInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'Assigned Dietitian'
            }),
            'progress': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill mb-2',
                'placeholder': 'Progress %'
            }),
        }
