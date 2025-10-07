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

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'subtitle', 'message']

