from django.shortcuts import render, get_object_or_404 , redirect
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils.timezone import localdate
from .forms import *

from app.models import *

# -------------------------
# Dashboard Home
# -------------------------
def dashboard_home(request):
    clients_total = UserProfile.objects.count()
    active_clients = UserProfile.objects.filter(activity_level__in=[
        "light", "moderate", "active", "extreme"]).count()
    starting_clients = UserProfile.objects.filter(goal__icontains="start").count()
    ending_clients = UserProfile.objects.filter(goal__icontains="end").count()

    context = {
        "page_title": "Dashboard Home",
        "pending_leads": 0,  # Extend with Leads model later
        "active_clients": active_clients,
        "starting_clients": starting_clients,
        "ending_clients": ending_clients,
        "total_clients": clients_total,
        "missed_payments": 0,
        "new_messages": 0,
    }
    return render(request, "home.html", context)

def leads_all(request):
    leads = Lead.objects.all().order_by("-created_at")

    # Create or update lead from modal form
    if request.method == "POST":
        lead_id = request.POST.get("lead_id")
        if lead_id:  # editing existing lead
            lead = get_object_or_404(Lead, pk=lead_id)
            form = LeadForm(request.POST, instance=lead)
        else:  # adding new lead
            form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("leads_all")

    else:
        form = LeadForm()

    return render(request, "leads.html", {
        "status": "All",
        "leads": leads,
        "form": form,
    })


def delete_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    lead.delete()
    return redirect("leads_all")
def leads_new(request):
    leads = Lead.objects.filter(status="New").order_by("-created_at")
    return render(request, "leads.html", {"status": "New", "leads": leads})

def leads_contacted(request):
    leads = Lead.objects.filter(status="Contacted").order_by("-created_at")
    return render(request, "leads.html", {"status": "Contacted", "leads": leads})

def leads_dialogue(request):
    leads = Lead.objects.filter(status="In Dialogue").order_by("-created_at")
    return render(request, "leads.html", {"status": "In Dialogue", "leads": leads})

def leads_onhold(request):
    leads = Lead.objects.filter(status="On Hold").order_by("-created_at")
    return render(request, "leads.html", {"status": "On Hold", "leads": leads})

def leads_won(request):
    leads = Lead.objects.filter(status="Won").order_by("-created_at")
    return render(request, "leads.html", {"status": "Won", "leads": leads})

def leads_lost(request):
    leads = Lead.objects.filter(status="Lost").order_by("-created_at")
    return render(request, "leads.html", {"status": "Lost", "leads": leads})
# -------------------------
# Clients
# -------------------------

def clients_active(request):
    """Show active clients - you'll need to define what 'active' means"""
    # Example: clients created in last 90 days and have a phone number
    profiles = UserProfile.objects.filter(
        created_at__gte=now()-timedelta(days=90),
        phone__isnull=False
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Active",
            "week": "Week 1",  # You'll need to calculate this based on your logic
            "checkin": "Pending",  # Add checkin status to your model
            "plans": "🥗",  # Add plans info to your model
            "reminders": "-",
            "days": "0"  # Days since last activity
        })
    
    return render(request, "clients.html", {"status": "Active", "clients": clients})

def clients_payment_error(request):
    """Clients with payment issues"""
    profiles = UserProfile.objects.filter(
        # Add payment_error field to your model or use existing fields
        # payment_error=True or status='payment_error'
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Payment Issue",
            "week": "Week 1",
            "checkin": "Overdue",
            "plans": "🥗",
            "reminders": "Payment",
            "days": "0"
        })
    
    return render(request, "clients.html", {"status": "Payment Error", "clients": clients})

def clients_started(request):
    """Show clients who are just starting"""
    profiles = UserProfile.objects.filter(
        created_at__gte=now()-timedelta(days=30)
    ).select_related("user")

    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        # Determine chat status based on profile data
        chat_status = "No account" if not profile.phone else "Offer Sent"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": chat_status,
            "start_day": f"{(now().date() - profile.created_at.date()).days} days ago",
            "created_at": profile.created_at.strftime("%d %B, %Y")
        })

    return render(request, "clients_started.html", {
        "status": "Starting",
        "clients": clients
    })
# views.py
def clients_offer_sent(request):
    """Show clients with offers sent"""
    profiles = UserProfile.objects.filter(
        phone__isnull=False
    ).select_related("user")

    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Offer Sent",
            "start_day": f"{(now().date() - profile.created_at.date()).days} days ago",
            "created_at": profile.created_at.strftime("%d %B, %Y")
        })

    return render(request, "clients_started.html", {
        "status": "Offer Sent",
        "clients": clients
    })

def clients_no_account(request):
    """Show clients with no account"""
    profiles = UserProfile.objects.filter(
        phone__isnull=True
    ).select_related("user")

    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "No Account",
            "start_day": f"{(now().date() - profile.created_at.date()).days} days ago",
            "created_at": profile.created_at.strftime("%d %B, %Y")
        })

    return render(request, "clients_started.html", {
        "status": "No Account",
        "clients": clients
    })
def clients_completed(request):
    """Show clients who completed programs"""
    # Filter based on your completion logic - add a 'status' or 'program_completed' field
    profiles = UserProfile.objects.filter(
        # status='completed' or program_ended=True
    ).select_related("user")

    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "-",
            "week": "Finished",
            "checkin": "Closed",
            "plans": "None",
            "reminders": "-"
        })

    return render(request, "clients_ended.html", {
        "status": "Ended",
        "clients": clients
    })

def clients_new_message(request):
    """Clients with new messages"""
    profiles = UserProfile.objects.filter(
        # Add last_message_read field or similar to track new messages
        # last_message__gt=F('last_message_read')
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "New Message",
            "week": "Week 1",
            "checkin": "Pending",
            "plans": "🥗",
            "reminders": "-",
            "days": "0"
        })
    
    return render(request, "clients.html", {"status": "New Message", "clients": clients})

def clients_new_checkin(request):
    """Clients with new check-ins pending"""
    profiles = UserProfile.objects.filter(
        # Add checkin_status field: checkin_status='pending'
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Check-in Ready",
            "week": "Week 1",
            "checkin": "New",
            "plans": "🥗",
            "reminders": "-",
            "days": "0"
        })
    
    return render(request, "clients.html", {"status": "New Check-In", "clients": clients})

def clients_missed_checkin(request):
    """Clients who missed check-ins"""
    profiles = UserProfile.objects.filter(
        # Add checkin_status field: checkin_status='missed'
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Missed",
            "week": "Week 1",
            "checkin": "Overdue",
            "plans": "🥗",
            "reminders": "Check-in",
            "days": "0"
        })
    
    return render(request, "clients.html", {"status": "Missed Check-In", "clients": clients})

def clients_reminders(request):
    """Clients with pending reminders"""
    profiles = UserProfile.objects.filter(
        # Add reminders field or last_reminder_sent logic
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Reminder",
            "week": "Week 1",
            "checkin": "Pending",
            "plans": "🥗",
            "reminders": "Due",
            "days": "0"
        })
    
    return render(request, "clients.html", {"status": "Reminders", "clients": clients})

def clients_no_communication(request):
    """Clients with no recent communication"""
    profiles = UserProfile.objects.filter(
        # Add last_communication field and filter for old dates
        # last_communication__lt=now()-timedelta(days=14)
    ).select_related("user")
    
    clients = []
    for profile in profiles:
        first_initial = profile.user.first_name[:1] if profile.user.first_name else ""
        last_initial = profile.user.last_name[:1] if profile.user.last_name else ""
        initials = (first_initial + last_initial).upper() or "??"
        
        days_no_comm = (now().date() - profile.last_communication.date()).days if profile.last_communication else 99
        
        clients.append({
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "No Contact",
            "week": "Week 1",
            "checkin": "Overdue",
            "plans": "🥗",
            "reminders": "Follow-up",
            "days": str(days_no_comm)
        })
    
    return render(request, "clients.html", {"status": "No Communication", "clients": clients})


# -------------------------
# Client Profile (with tabs)
# -------------------------
def client_profile(request, client_id):
    user = get_object_or_404(User, id=client_id)
    profile = get_object_or_404(UserProfile, user=user)

    workouts = Workout.objects.filter(user=user).order_by("-date")
    workout_logs = UserWorkoutLog.objects.filter(user=user).order_by("-date")
    meal_logs = UserMealLog.objects.filter(user=user).order_by("-date")
    meals = Meal.objects.all().order_by("meal_type")
    progress_entries = Progress.objects.filter(user=user).order_by("-date")
    wishlist = WishlistItem.objects.filter(user=user).order_by("-priority")

    context = {
        "client": profile,
        "workouts": workouts,
        "workout_logs": workout_logs,
        "meal_logs": meal_logs,
        "meals": meals,
        "progress": progress_entries,
        "wishlist": wishlist,
        "current_tab": request.GET.get("tab", "overview"),
    }
    return render(request, "client_profile.html", context)


# -------------------------
# Nutrition
# -------------------------
def nutrition(request):
    """Ingredients page - showing all meals"""
    meals = Nutrition.objects.all()
    return render(request, "nutrition.html", {
        "meals": meals,
        "active_tab": "ingredients"
    })

def nutrition_recipes(request):
    """Recipes page - showing all meals"""
    meals = Nutrition.objects.all()
    return render(request, "nutrition_recipes.html", {
        "meals": meals,
        "active_tab": "recipes"
    })

def nutrition_templates(request):
    """Templates page"""
    return render(request, "nutrition_templates.html", {
        "active_tab": "templates"
    })

# -------------------------
# Workouts
# -------------------------
# views.py (workouts section)
def workouts(request):
    # Which tab should be active after reload
    active_tab = request.GET.get("tab", "exercises")

    # Exercises filters
    q_ex = request.GET.get("q_ex", "").strip()
    muscle = request.GET.get("muscle", "")
    library = request.GET.get("library", "all")  # all | pre | own

    exercises = Exercise.objects.select_related("primary_muscle").order_by("name")
    if q_ex:
        exercises = exercises.filter(
            Q(name__icontains=q_ex) |
            Q(primary_muscle__name__icontains=q_ex) |
            Q(equipment__icontains=q_ex)
        )
    if muscle:
        exercises = exercises.filter(primary_muscle__group=muscle)
    if library == "pre":
        exercises = exercises.filter(created_by__isnull=True)
    elif library == "own":
        exercises = exercises.filter(created_by=request.user)

    exercises_count = exercises.count()
    muscle_groups = Muscle._meta.get_field("group").choices

    # Templates (group by workout name)
    q_tpl = request.GET.get("q_tpl", "").strip()
    templates = Workout.objects.values("name").annotate(sessions=Count("id")).order_by("name")
    if q_tpl:
        templates = templates.filter(name__icontains=q_tpl)
    templates_count = templates.count()

    return render(request, "workouts.html", {
        "active_tab": active_tab,
        "exercises": exercises[:500],  # cap for page performance; add pagination later if needed
        "exercises_count": exercises_count,
        "muscle_groups": muscle_groups,
        "q_ex": q_ex,
        "muscle": muscle,
        "library": library,

        "templates": templates,
        "templates_count": templates_count,
        "q_tpl": q_tpl,
    })
def workout_new(request):
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        formset = WorkoutExerciseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            workout = form.save()
            formset.instance = workout
            formset.save()
            messages.success(request, "Workout created.")
            return redirect("workouts")
    else:
        form = WorkoutForm(initial={"date": localdate(), "completed": False})
        formset = WorkoutExerciseFormSet()
    return render(request, "workout_form.html", {"form": form, "formset": formset, "is_new": True})

def workout_edit(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
        form = WorkoutForm(request.POST, instance=workout)
        formset = WorkoutExerciseFormSet(request.POST, instance=workout)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Workout updated.")
            return redirect("workouts")
    else:
        form = WorkoutForm(instance=workout)
        formset = WorkoutExerciseFormSet(instance=workout)
    return render(request, "workout_form.html", {"form": form, "formset": formset, "workout": workout})

def workout_delete(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
        workout.delete()
        messages.success(request, "Workout deleted.")
        return redirect("workouts")
    return render(request, "confirm_delete.html", {"object": workout, "title": "Delete workout"})


def workout_toggle_complete(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    workout.completed = not workout.completed
    workout.save(update_fields=["completed"])
    messages.success(request, f"Marked as {'completed' if workout.completed else 'incomplete'}.")
    return redirect("workouts")

def workout_duplicate(request, pk):
    src = get_object_or_404(Workout, pk=pk)
    # duplicate workout
    new_w = Workout.objects.create(
        user=src.user,
        name=f"{src.name} (copy)",
        description=src.description,
        duration=src.duration,
        level=src.level,
        calories_burned=src.calories_burned,
        date=localdate(),
        completed=False,
    )
    # duplicate its exercises
    items = src.items.all()
    for it in items:
        it.pk = None
        it.workout = new_w
        it.save()
    messages.success(request, "Workout duplicated.")
    return redirect("workout_edit", pk=new_w.pk)

# -------------------------
# Progress
# -------------------------
def progress_list(request):
    entries = Progress.objects.all().order_by("-date")
    return render(request, "progress.html", {"progress_entries": entries})


# -------------------------
# Meals
# -------------------------
def meals(request):
    meals = Meal.objects.all()
    return render(request, "meals.html", {"meals": meals})


# -------------------------
# Wishlist
# -------------------------
def wishlist_list(request):
    wishlist = WishlistItem.objects.all().order_by("-priority")
    return render(request, "wishlist.html", {"wishlist": wishlist})


# -------------------------
# Content (static for now)
def content(request):
    files = File.objects.all().order_by('-created_at')
    lessons = Lesson.objects.all().order_by('-created_at')

    file_form = FileForm()
    lesson_form = LessonForm()

    return render(request, 'content.html', {
        'files': files,
        'lessons': lessons,
        'file_form': file_form,
        'lesson_form': lesson_form,
    })


# ---------- FILE CRUD ----------
def add_file(request):
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    return redirect('content')


def edit_file(request, pk):
    file = get_object_or_404(File, pk=pk)
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES, instance=file)
        if form.is_valid():
            form.save()
            return redirect('content')
    return redirect('content')


def delete_file(request, pk):
    file = get_object_or_404(File, pk=pk)
    file.delete()
    return redirect('content')


# ---------- LESSON CRUD ----------
def add_lesson(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('content')


def edit_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('content')
    return redirect('content')


def delete_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    lesson.delete()
    return redirect('content')