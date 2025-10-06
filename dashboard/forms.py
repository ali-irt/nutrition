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
        fields = ['title', 'description', 'file']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'subtitle', 'message']

