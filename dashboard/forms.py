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