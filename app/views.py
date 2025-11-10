# views.py - COMPLETE VERSION
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Q, Count, Max
from datetime import datetime, date, timedelta
import random
import string, json
import time
from .serializers import *
from .models import *
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# ============================================
# AUTH VIEWS
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def Register(request):
    """User registration"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user_id': user.id,
            'email': user.email,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'onboarding_completed': False
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    """Login with username, email, or phone"""
    identifier = request.data.get('identifier')
    password = request.data.get('password')

    if not identifier or not password:
        return Response(
            {'error': 'Both identifier and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Try to find the user by username, email, or phone number
    try:
        user = User.objects.filter(
            Q(username__iexact=identifier) |
            Q(email__iexact=identifier)         ).first()
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if user and user.check_password(password):
        refresh = RefreshToken.for_user(user)
        onboarding_completed = hasattr(user, 'profile') and user.profile.onboarding_completed
        return Response({
            'user_id': user.id,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'onboarding_completed': onboarding_completed
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user and delete token"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_otp(request):
    """Send OTP for verification"""
    channel = request.data.get('channel', 'phone')
    destination = request.data.get('phone') or request.data.get('email')
    
    if not destination:
        return Response({'error': 'Destination required'}, status=status.HTTP_400_BAD_REQUEST)
    
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = timezone.now() + timedelta(minutes=10)
    
    OTP.objects.filter(user=request.user, destination=destination).delete()
    
    OTP.objects.create(
        user=request.user,
        channel=channel,
        destination=destination,
        code=code,
        expires_at=expires_at
    )
    
    print(f"OTP for {destination}: {code}")  # TODO: Send actual SMS/Email
    
    return Response({'message': 'OTP sent successfully', 'expires_at': expires_at})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    """Verify OTP"""
    destination = request.data.get('phone') or request.data.get('email')
    code = request.data.get('code')
    
    try:
        otp = OTP.objects.get(user=request.user, destination=destination, code=code)
        
        if not otp.is_valid():
            return Response({'error': 'OTP expired or already used'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp.used_at = timezone.now()
        otp.save()
        
        profile = request.user.profile
        if otp.channel == 'phone':
            profile.phone_verified = True
        else:
            profile.email_verified = True
        profile.save()
        
        return Response({
            'verified': True,
            'message': f'{otp.channel.title()} verified successfully'
        })
    except OTP.DoesNotExist:
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password (JWT version)"""
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    # Validate input
    if not old_password or not new_password:
        return Response({'error': 'Both old and new passwords are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Check old password
    if not request.user.check_password(old_password):
        return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate new password
    if len(new_password) < 8:
        return Response({'error': 'Password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)

    # Save new password
    request.user.set_password(new_password)
    request.user.save()

    # Issue new JWT tokens (refresh + access)
    refresh = RefreshToken.for_user(request.user)

    return Response({
        'message': 'Password changed successfully',
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send password reset OTP"""
    email = request.data.get('email')
    
    try:
        user = User.objects.get(email=email)
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=15)
        
        OTP.objects.filter(user=user, channel='email').delete()
        OTP.objects.create(
            user=user,
            channel='email',
            destination=email,
            code=code,
            expires_at=expires_at
        )
        
        print(f"Password reset OTP for {email}: {code}")  # TODO: Send email
        
        return Response({'message': 'Reset code sent to email', 'expires_at': expires_at})
    except User.DoesNotExist:
        return Response({'message': 'If email exists, reset code has been sent'})



@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using OTP (JWT version)"""
    email = request.data.get('email')
    code = request.data.get('code')
    new_password = request.data.get('new_password')

    # Validate required fields
    if not all([email, code, new_password]):
        return Response({'error': 'Email, code, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        otp = OTP.objects.get(user=user, channel='email', destination=email, code=code)

        # Check OTP validity
        if not otp.is_valid():
            return Response({'error': 'OTP expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)

        # Update user password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp.used_at = timezone.now()
        otp.save()

        # Generate new JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Password reset successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    except (User.DoesNotExist, OTP.DoesNotExist):
        return Response({'error': 'Invalid email or code'}, status=status.HTTP_400_BAD_REQUEST)
 # PROFILE VIEWSET
# ============================================

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        """Create profile during onboarding"""
        serializer = UserProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            profile = serializer.save()
            response_serializer = UserProfileSerializer(profile)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# DASHBOARD VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_today(request):
    """Get today's dashboard summary"""
    user = request.user
    today = date.today()
    
    # Get daily macro target
    try:
        daily_target = DailyMacroTarget.objects.get(user=user, date=today)
    except DailyMacroTarget.DoesNotExist:
        active_plan = MacroPlan.objects.filter(user=user, active=True).first()
        if active_plan:
            daily_target = DailyMacroTarget.objects.create(
                user=user, date=today,
                calorie_target=active_plan.calorie_target,
                protein_g=active_plan.protein_g,
                carbs_g=active_plan.carbs_g,
                fats_g=active_plan.fats_g
            )
        else:
            daily_target = None
    
    # Calculate consumed nutrition
    food_entries = FoodDiaryEntry.objects.filter(user=user, date=today)
    consumed_calories = consumed_protein = consumed_carbs = consumed_fats = 0
    
    for entry in food_entries:
        if entry.food:
            consumed_calories += entry.food.calories * entry.servings
            consumed_protein += entry.food.protein * entry.servings
            consumed_carbs += entry.food.carbs * entry.servings
            consumed_fats += entry.food.fat * entry.servings
        elif entry.meal:
            consumed_calories += entry.meal.calories * entry.servings
            consumed_protein += entry.meal.protein * entry.servings
            consumed_carbs += entry.meal.carbs * entry.servings
            consumed_fats += entry.meal.fats * entry.servings
    
    # Burned calories
    workout_logs = UserWorkoutLog.objects.filter(user=user, date=today, completed=True)
    burned_calories = sum([log.calories_burned or 0 for log in workout_logs])
    
    activity_summary = DailyActivitySummary.objects.filter(user=user, date=today).first()
    if activity_summary:
        burned_calories += activity_summary.calories_burned
    
    # Water
    total_water = WaterLog.objects.filter(user=user, date=today).aggregate(
        Sum('amount_ml'))['amount_ml__sum'] or 0
    
    # Steps
    steps = activity_summary.steps if activity_summary else 0
    
    # Workouts
    scheduled_workouts = Workout.objects.filter(user=user, date=today)
    completed_workouts = workout_logs.count()
    next_workout = scheduled_workouts.filter(completed=False).first()
    
    # Sleep
    last_checkin = Checkin.objects.filter(user=user).order_by('-date').first()
    
    profile = user.profile
    
    return Response({
        'date': today,
        'user': {
            'name': f"{user.first_name} {user.last_name}",
            'current_weight': float(profile.weight),
            'goal_weight': float(profile.target_weight) if profile.target_weight else None,
            'progress_percentage': 60
        },
        'calories': {
            'target': daily_target.calorie_target if daily_target else 2000,
            'consumed': round(consumed_calories),
            'burned': burned_calories,
            'remaining': round((daily_target.calorie_target if daily_target else 2000) - consumed_calories + burned_calories)
        },
        'macros': {
            'protein': {'target': daily_target.protein_g if daily_target else 150, 'consumed': round(consumed_protein)},
            'carbs': {'target': daily_target.carbs_g if daily_target else 200, 'consumed': round(consumed_carbs)},
            'fats': {'target': daily_target.fats_g if daily_target else 65, 'consumed': round(consumed_fats)}
        },
        'water': {
            'target_ml': profile.daily_water_goal_ml,
            'consumed_ml': total_water,
            'percentage': round((total_water / profile.daily_water_goal_ml) * 100, 1)
        },
        'steps': {
            'target': profile.daily_step_goal,
            'current': steps,
            'percentage': round((steps / profile.daily_step_goal) * 100, 1)
        },
        'workouts': {
            'completed': completed_workouts,
            'scheduled': scheduled_workouts.count(),
            'next_workout': {'id': next_workout.id, 'name': next_workout.name, 'time': '18:00'} if next_workout else None
        },
        'sleep': {
            'last_night_hours': float(last_checkin.sleep_hours) if last_checkin and last_checkin.sleep_hours else None,
            'goal_hours': float(profile.sleep_goal_hours) if profile.sleep_goal_hours else 8
        }
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_progress(request):
    """Get weekly progress summary (optionally by ?week_start=YYYY-MM-DD)"""
    user = request.user

    # Optional query param: week_start
    week_start_str = request.query_params.get('week_start')
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    daily_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)

        # Food entries
        food_entries = FoodDiaryEntry.objects.filter(user=user, date=day)
        calories = sum([
            (entry.food.calories if entry.food else entry.meal.calories) * entry.servings
            for entry in food_entries
        ])

        # Steps
        activity = DailyActivitySummary.objects.filter(user=user, date=day).first()
        steps = activity.steps if activity else 0

        # Weight
        progress = Progress.objects.filter(user=user, date=day).first()
        weight = float(progress.weight) if progress else None

        # Workouts
        workout_completed = UserWorkoutLog.objects.filter(user=user, date=day, completed=True).exists()

        daily_data.append({
            'date': day,
            'weight': weight,
            'calories': round(calories),
            'steps': steps,
            'workout_completed': workout_completed
        })

    total_calories = sum([d['calories'] for d in daily_data])
    total_steps = sum([d['steps'] for d in daily_data])
    workouts_completed = sum([1 for d in daily_data if d['workout_completed']])

    weights = [d['weight'] for d in daily_data if d['weight']]
    weight_change = weights[-1] - weights[0] if len(weights) >= 2 else 0

    return Response({
        'week_start': week_start,
        'week_end': week_end,
        'weight_change': round(weight_change, 1),
        'workouts_completed': workouts_completed,
        'workouts_target': user.profile.workouts_per_week,
        'avg_calories': round(total_calories / 7) if total_calories else 0,
        'avg_steps': round(total_steps / 7) if total_steps else 0,
        'daily_data': daily_data
    })


# ============================================
# FOOD & MEAL VIEWSETS
# ============================================
class FoodViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Food.objects.all()
        search = self.request.query_params.get('q', None)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(brand__name__icontains=search))
        if self.action == 'list':  # only limit when listing
            queryset = queryset[:20]
        return queryset

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_custom(self, request):
        """Create a custom food item"""
        serializer = FoodSerializer(data=request.data)
        if serializer.is_valid():
            food = serializer.save(created_by=request.user, is_custom=True)
            return Response(FoodSerializer(food).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def scan_barcode(self, request):
        """Scan barcode and return food"""
        barcode = request.data.get('barcode')
        if not barcode:
            return Response({'error': 'Barcode required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            food_barcode = FoodBarcode.objects.get(code=barcode)
            serializer = self.get_serializer(food_barcode.food)
            return Response({'found': True, 'food': serializer.data})
        except FoodBarcode.DoesNotExist:
            return Response({'found': False, 'message': 'Food not found'})


class FoodDiaryViewSet(viewsets.ModelViewSet):
    serializer_class = FoodDiaryEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FoodDiaryEntry.objects.filter(user=self.request.user)
        date_param = self.request.query_params.get('date', None)
        if date_param:
            queryset = queryset.filter(date=date_param)
        return queryset.order_by('-date', '-time')
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def diary(self, request):
        """Get meal diary for a specific date"""
        date_param = request.query_params.get('date', date.today())
        if isinstance(date_param, str):
            date_param = datetime.strptime(date_param, '%Y-%m-%d').date()
        
        entries = FoodDiaryEntry.objects.filter(user=request.user, date=date_param)
        
        meals = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
        total_calories = total_protein = total_carbs = total_fats = 0
        
        for entry in entries:
            serializer = self.get_serializer(entry)
            data = serializer.data
            meals[entry.meal_time].append(data)
            
            total_calories += data['total_calories']
            total_protein += data['total_protein']
            total_carbs += data['total_carbs']
            total_fats += data['total_fats']
        
        return Response({
            'date': date_param,
            'total_calories': round(total_calories),
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fats': round(total_fats, 1),
            'meals': meals
        })

 
class MealViewSet(viewsets.ReadOnlyModelViewSet):
    """API for listing meals and fetching weekly menus"""
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated]
    queryset = Meal.objects.all()

    def get_queryset(self):
        queryset = Meal.objects.all()
        # optional filters
        meal_type = self.request.query_params.get('type')
        vegan = self.request.query_params.get('vegan')
        search = self.request.query_params.get('q')

        if meal_type:
            queryset = queryset.filter(meal_type__iexact=meal_type)
        if vegan == 'true':
            queryset = queryset.filter(is_vegan=True)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    @action(detail=False, methods=['get'])
    def menu(self, request):
        """Get the weekly menu based on week_start"""
        week_start = request.query_params.get('week_start')

        if not week_start:
            week_start = timezone.now().date()
        else:
            try:
                week_start = timezone.datetime.strptime(week_start, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        week_end = week_start + timedelta(days=6)
        meals = self.get_queryset()

        serializer = self.get_serializer(meals, many=True)
        return Response({
            "week_start": week_start,
            "week_end": week_end,
            "available_meals": serializer.data
        })


# ============================================
# WORKOUT VIEWSETS
# ============================================
class WorkoutViewSet(viewsets.ModelViewSet):
    """
    Workout templates and plans
    Corresponds to: Personalized Plan screen showing weekly workout schedule
    """
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def weekly_plan(self, request):
        """Get workouts for current week"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        workouts = Workout.objects.filter(
            user=request.user,
            date__range=[week_start, week_end]
        ).order_by('date')
        
        serializer = self.get_serializer(workouts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_muscle_group(self, request):
        """
        Get workouts filtered by muscle group
        Corresponds to: Chest screen showing chest-specific exercises
        """
        muscle_group = request.query_params.get('group', '')
        
        if muscle_group:
            # Get exercises for this muscle group
            exercises = Exercise.objects.filter(
                Q(primary_muscle__group=muscle_group) |
                Q(secondary_muscles__group=muscle_group)
            ).distinct()
            
            # Get workouts containing these exercises
            workouts = Workout.objects.filter(
                user=request.user,
                items__exercise__in=exercises
            ).distinct()
        else:
            workouts = self.get_queryset()
        
        serializer = self.get_serializer(workouts, many=True)
        return Response(serializer.data)
    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Exercise library
    Corresponds to: Activity selection and chest exercise screens
    """
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Exercise.objects.all()
    
    @action(detail=False, methods=['get'])
    def by_muscle(self, request):
        """Filter exercises by muscle group"""
        muscle_group = request.query_params.get('group')
        
        if muscle_group:
            exercises = Exercise.objects.filter(
                Q(primary_muscle__group=muscle_group) |
                Q(secondary_muscles__group=muscle_group)
            ).distinct()
        else:
            exercises = self.queryset
        
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most logged exercises"""
        popular_exercises = Exercise.objects.annotate(
            log_count=Count('setlog')
        ).order_by('-log_count')[:20]
        
        serializer = self.get_serializer(popular_exercises, many=True)
        return Response(serializer.data)



class MuscleViewSet(viewsets.ReadOnlyModelViewSet):
    """Muscle groups and muscles"""
    serializer_class = MuscleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Muscle.objects.all()
    
    @action(detail=False, methods=['get'])
    def groups(self, request):
        """Get all muscle groups"""
        groups = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Muscle._meta.get_field('group').choices
        ]
        return Response(groups)


class UserWorkoutLogViewSet(viewsets.ModelViewSet):
    """
    User's workout logs and tracking
    Corresponds to: Workout tracking with sets, reps, weights
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkoutLogCreateSerializer
        return UserWorkoutLogSerializer
    
    def get_queryset(self):
        return UserWorkoutLog.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a workout session"""
        workout_log = self.get_object()
        workout_log.start_time = timezone.now().time()
        workout_log.save()
        
        serializer = self.get_serializer(workout_log)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a workout session"""
        workout_log = self.get_object()
        workout_log.end_time = timezone.now().time()
        workout_log.completed = True
        workout_log.save()
        
        serializer = self.get_serializer(workout_log)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_set(self, request, pk=None):
        """
        Add a set log to this workout session
        Body: {exercise_id, order, set_number, reps, weight_kg, rpe, etc.}
        """
        workout_log = self.get_object()
        
        data = request.data.copy()
        data['session'] = workout_log.id
        
        serializer = SetLogCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get workout history with pagination"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        queryset = queryset.order_by('-date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)




class SetLogViewSet(viewsets.ModelViewSet):
    """Individual set tracking"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SetLogCreateSerializer
        return SetLogSerializer
    
    def get_queryset(self):
        return SetLog.objects.filter(session__user=self.request.user)



class MealBoxViewSet(viewsets.ModelViewSet):
    serializer_class = MealBoxSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealBox.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get current active meal box (this week)"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        box, created = MealBox.objects.get_or_create(user=request.user, week_start=week_start, defaults={'name': 'Weekly Box'})
        serializer = self.get_serializer(box)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add(self, request, pk=None):
        """Add meal to the box"""
        box = self.get_object()
        meal_id = request.data.get('meal_id')
        quantity = int(request.data.get('quantity', 1))

        meal = get_object_or_404(Meal, id=meal_id)
        item, created = MealBoxItem.objects.get_or_create(meal_box=box, meal=meal)
        item.quantity = item.quantity + quantity if not created else quantity
        item.save()

        return Response({'message': 'Meal added successfully', 'item_id': item.id}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        """Remove a meal from the box"""
        box = self.get_object()
        meal_id = request.data.get('meal_id')

        meal = get_object_or_404(Meal, id=meal_id)
        MealBoxItem.objects.filter(meal_box=box, meal=meal).delete()

        return Response({'message': 'Meal removed successfully'}, status=status.HTTP_200_OK)

 
# ============================================
# PROGRESS VIEWSET
# ============================================

class ProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Progress.objects.filter(user=self.request.user)
        from_date = self.request.query_params.get('from', None)
        to_date = self.request.query_params.get('to', None)
        
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)
        
        return queryset.order_by('-date')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        summary = {}
        if queryset.count() >= 2:
            first = queryset.last()
            latest = queryset.first()
            
            weight_change = float(latest.weight) - float(first.weight)
            weight_change_pct = (weight_change / float(first.weight)) * 100
            
            summary = {
                'weight_change': round(weight_change, 1),
                'weight_change_percentage': round(weight_change_pct, 1),
                'body_fat_change': round(float(latest.body_fat_percentage) - float(first.body_fat_percentage), 1) if first.body_fat_percentage and latest.body_fat_percentage else None,
                'muscle_gain': round(float(latest.muscle_mass) - float(first.muscle_mass), 1) if first.muscle_mass and latest.muscle_mass else None
            }
        
        return Response({'entries': serializer.data, 'summary': summary})
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Get progress photos"""
        progress = self.get_object()
        return Response({
            'date': progress.date,
            'front_image': request.build_absolute_uri(progress.front_image.url) if progress.front_image else None,
            'side_image': request.build_absolute_uri(progress.side_image.url) if progress.side_image else None,
            'back_image': request.build_absolute_uri(progress.back_image.url) if progress.back_image else None
        })


# ============================================
# WATER & ACTIVITY VIEWSETS
# ============================================

class WaterLogViewSet(viewsets.ModelViewSet):
    serializer_class = WaterLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return WaterLog.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        today = date.today()
        total_today = WaterLog.objects.filter(user=request.user, date=today).aggregate(
            Sum('amount_ml'))['amount_ml__sum'] or 0
        
        goal = request.user.profile.daily_water_goal_ml
        
        response.data.update({
            'total_today': total_today,
            'goal': goal,
            'remaining': max(0, goal - total_today)
        })
        
        return response
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's water intake"""
        today = date.today()
        logs = WaterLog.objects.filter(user=request.user, date=today).order_by('created_at')
        
        total_ml = logs.aggregate(Sum('amount_ml'))['amount_ml__sum'] or 0
        goal_ml = request.user.profile.daily_water_goal_ml
        
        return Response({
            'date': today,
            'total_ml': total_ml,
            'goal_ml': goal_ml,
            'percentage': round((total_ml / goal_ml) * 100, 1) if goal_ml else 0,
            'logs': [{'time': log.created_at.strftime('%H:%M'), 'amount_ml': log.amount_ml} for log in logs]
        })


class DailyActivityViewSet(viewsets.ModelViewSet):
    serializer_class = DailyActivitySummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DailyActivitySummary.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def sync_steps(self, request):
        """Sync steps from fitness tracker"""
        date_param = request.data.get('date', date.today())
        steps = request.data.get('steps', 0)
        calories = request.data.get('calories_burned', 0)
        distance = request.data.get('distance_m', 0)
        
        activity, created = DailyActivitySummary.objects.update_or_create(
            user=request.user,
            date=date_param,
            defaults={'steps': steps, 'calories_burned': calories, 'distance_m': distance}
        )
        
        goal = request.user.profile.daily_step_goal
        
        return Response({
            'synced': True,
            'goal': goal,
            'percentage': round((steps / goal) * 100, 1) if goal else 0
        })
    
    @action(detail=False, methods=['get'])
    def steps_today(self, request):
        """Get today's steps"""
        date_param = request.query_params.get('date', date.today())
        
        try:
            activity = DailyActivitySummary.objects.get(user=request.user, date=date_param)
            serializer = self.get_serializer(activity)
            data = serializer.data
        except DailyActivitySummary.DoesNotExist:
            data = {
                'date': date_param,
                'steps': 0,
                'calories_burned': 0,
                'distance_m': 0
            }
        
        goal = request.user.profile.daily_step_goal
        data['goal'] = goal
        data['percentage'] = round((data['steps'] / goal) * 100, 1) if goal else 0
        
        return Response(data)


# ============================================
# CHECKIN VIEWSETS
# ============================================

class CheckinFormViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CheckinFormSerializer
    permission_classes = [IsAuthenticated]
    queryset = CheckinForm.objects.filter(active=True)

class CheckinViewSet(viewsets.ModelViewSet):
    serializer_class = CheckinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Checkin.objects.filter(user=self.request.user).order_by('-date')
    
    def perform_create(self, serializer):
        checkin = serializer.save(user=self.request.user)
        
        # Handle answers
        answers_data = self.request.data.get('answers', [])

        # If it's a string (e.g. JSON array as string), parse it
        if isinstance(answers_data, str):
            try:
                answers_data = json.loads(answers_data)
            except json.JSONDecodeError:
                answers_data = []

        for answer_data in answers_data:
            if isinstance(answer_data, dict):
                CheckinAnswer.objects.create(
                    checkin=checkin,
                    question_id=answer_data.get('question_id'),
                    value=answer_data.get('value')
                )
        
        # Handle photos
        for kind in ['front', 'side', 'back']:
            photo_key = f'{kind}_photo'
            if photo_key in self.request.FILES:
                CheckinPhoto.objects.create(
                    checkin=checkin,
                    kind=kind,
                    image=self.request.FILES[photo_key]
                )

# ============================================
# CARDIO VIEWSET
# ============================================

class CardioSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CardioSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CardioSession.objects.filter(user=self.request.user)
        activity = self.request.query_params.get('activity', None)
        from_date = self.request.query_params.get('from', None)
        to_date = self.request.query_params.get('to', None)
        
        if activity:
            queryset = queryset.filter(activity=activity)
        if from_date:
            queryset = queryset.filter(started_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(started_at__date__lte=to_date)
        
        return queryset.order_by('-started_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
   

    @action(detail=True, methods=['patch'])
    def finish(self, request, pk=None):
        """Finish cardio session"""
        session = self.get_object()

        # --- Convert ended_at to datetime safely ---
        ended_at_str = request.data.get('ended_at')
        if ended_at_str:
            try:
                # Parse ISO 8601 datetime string (e.g. "2025-10-25T17:30:00")
                ended_at_dt = datetime.fromisoformat(ended_at_str)
                # Make timezone aware if not already
                if ended_at_dt.tzinfo is None:
                    ended_at_dt = make_aware(ended_at_dt)
                session.ended_at = ended_at_dt
            except Exception as e:
                return Response(
                    {"error": f"Invalid ended_at format. Expected ISO 8601. ({e})"},
                    status=400
                )

        # --- Update other optional fields ---
        session.distance_m = request.data.get('distance_m', session.distance_m)
        session.calories = request.data.get('calories', session.calories)
        session.avg_hr = request.data.get('avg_hr', session.avg_hr)
        session.notes = request.data.get('notes', session.notes)
        session.save()

        # --- Duration and average pace calculation ---
        duration = session.duration
        avg_pace = None
        if duration and session.distance_m and session.distance_m > 0:
            total_minutes = duration.total_seconds() / 60
            km = session.distance_m / 1000
            pace_minutes = total_minutes / km
            avg_pace = f"{int(pace_minutes)}:{int((pace_minutes % 1) * 60):02d}"

        return Response({
            "completed": True,
            "duration": str(duration) if duration else None,
            "avg_pace_per_km": avg_pace
        })



# ============================================
# HEART RATE VIEWSET
# ============================================

class HeartRateViewSet(viewsets.ModelViewSet):
    serializer_class = HeartRateSampleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = HeartRateSample.objects.filter(user=self.request.user)
        from_ts = self.request.query_params.get('from', None)
        to_ts = self.request.query_params.get('to', None)
        
        if from_ts:
            queryset = queryset.filter(ts__gte=from_ts)
        if to_ts:
            queryset = queryset.filter(ts__lte=to_ts)
        
        return queryset.order_by('ts')
    
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Bulk sync heart rate samples"""
        samples = request.data.get('samples', [])
        
        created_count = 0
        for sample in samples:
            HeartRateSample.objects.create(
                user=request.user,
                ts=sample['ts'],
                bpm=sample['bpm']
            )
            created_count += 1
        
        return Response({'synced': created_count})
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        bpms = [sample.bpm for sample in queryset]
        stats = {
            'avg_bpm': round(sum(bpms) / len(bpms)) if bpms else 0,
            'max_bpm': max(bpms) if bpms else 0,
            'min_bpm': min(bpms) if bpms else 0
        }
        
        return Response({'samples': serializer.data, **stats})


# ============================================
# RECIPE VIEWSET
# ============================================

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Recipe.objects.all()
        is_public = self.request.query_params.get('is_public', None)
        search = self.request.query_params.get('search', None)
        
        if is_public == 'true':
            queryset = queryset.filter(is_public=True)
        else:
            queryset = queryset.filter(Q(created_by=self.request.user) | Q(is_public=True))
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        recipe = serializer.save(created_by=self.request.user)
        
        # Create ingredients
        ingredients_data = self.request.data.get('ingredients', [])
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                food_id=ingredient['food_id'],
                grams=ingredient['grams']
            )


# ============================================
# MACRO PLAN VIEWSET
# ============================================

class MacroPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MacroPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MacroPlan.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        MacroPlan.objects.filter(user=self.request.user, active=True).update(active=False)
        serializer.save(user=self.request.user, active=True)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate macros based on user profile"""
        profile = request.user.profile
        goal = request.data.get('goal', profile.goal)
        activity_level = request.data.get('activity_level', profile.activity_level)
        goal_rate = request.data.get('goal_rate_lbs_per_week', profile.goal_rate_lbs_per_week or 1.0)
        
        # Calculate BMR
        weight_kg = float(profile.weight)
        height_cm = float(profile.height)
        age = profile.age
        
        if profile.unit_system == 'imperial':
            weight_kg = weight_kg * 0.453592
            height_cm = height_cm * 2.54
        
        if profile.gender == 'male':
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        
        # Calculate TDEE
        activity_multipliers = {
            'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55,
            'active': 1.725, 'extreme': 1.9
        }
        tdee = bmr * activity_multipliers.get(activity_level, 1.55)
        
        # Adjust for goal
        calorie_target = tdee
        if 'lose' in goal.lower():
            deficit = float(goal_rate) * 3500 / 7
            calorie_target = tdee - deficit
        elif 'gain' in goal.lower():
            surplus = float(goal_rate) * 3500 / 7
            calorie_target = tdee + surplus
        
        # Calculate macros
        protein_g = weight_kg * 2.2
        fat_calories = calorie_target * 0.25
        fats_g = fat_calories / 9
        protein_calories = protein_g * 4
        carb_calories = calorie_target - protein_calories - fat_calories
        carbs_g = carb_calories / 4
        
        return Response({
            'bmr': round(bmr),
            'tdee': round(tdee),
            'calorie_target': round(calorie_target),
            'protein_g': round(protein_g),
            'carbs_g': round(carbs_g),
            'fats_g': round(fats_g),
            'protein_percentage': round((protein_calories / calorie_target) * 100),
            'carbs_percentage': round((carb_calories / calorie_target) * 100),
            'fats_percentage': round((fat_calories / calorie_target) * 100)
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active macro plan"""
        plan = MacroPlan.objects.filter(user=request.user, active=True).first()
        if not plan:
            return Response({'message': 'No active macro plan'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data)


class DailyMacroTargetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyMacroTargetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DailyMacroTarget.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        date_param = request.query_params.get('date', date.today())
        
        try:
            target = DailyMacroTarget.objects.get(user=request.user, date=date_param)
            serializer = self.get_serializer(target)
            return Response(serializer.data)
        except DailyMacroTarget.DoesNotExist:
            return Response({'message': 'No target for this date'}, status=status.HTTP_404_NOT_FOUND)


# ============================================
# SUBSCRIPTION & MEAL PLAN VIEWSETS
# ============================================

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = Plan.objects.filter(product__active=True).order_by('sort_order')


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        address = serializer.save(user=self.request.user)
        
        if address.is_default:
            Address.objects.filter(user=self.request.user).exclude(
                id=address.id
            ).update(is_default=False)


class MealSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = MealSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MealSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active subscription"""
        subscription = MealSubscription.objects.filter(
            user=request.user,
            status='active'
        ).first()
        
        if not subscription:
            return Response({'message': 'No active subscription'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(subscription)
        data = serializer.data
        
        deliveries = Delivery.objects.filter(
            subscription=subscription,
            scheduled_date__gte=date.today()
        ).order_by('scheduled_date')[:5]
        
        data['upcoming_deliveries'] = DeliverySerializer(deliveries, many=True).data
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def select_meals(self, request, pk=None):
        """Select meals for a specific week"""
        subscription = self.get_object()
        week_start = request.data.get('week_start')
        selections = request.data.get('selections', [])
        
        WeeklyMealSelection.objects.filter(
            subscription=subscription,
            week_start=week_start
        ).delete()
        
        total_meals = 0
        for selection in selections:
            WeeklyMealSelection.objects.create(
                subscription=subscription,
                week_start=week_start,
                meal_id=selection['meal_id'],
                quantity=selection['quantity']
            )
            total_meals += selection['quantity']
        
        return Response({'saved': True, 'total_meals': total_meals})


class MealOrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MealOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MealOrder.objects.filter(customer=self.request.user)
        status_param = self.request.query_params.get('status', None)
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.order_by('-created_at')


class DeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Delivery.objects.filter(
            subscription__user=self.request.user
        ).order_by('-scheduled_date')
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming deliveries"""
        deliveries = Delivery.objects.filter(
            subscription__user=request.user,
            scheduled_date__gte=date.today(),
            status__in=['scheduled', 'out_for_delivery']
        ).order_by('scheduled_date')
        
        serializer = self.get_serializer(deliveries, many=True)
        return Response({'deliveries': serializer.data})


# ============================================
# PAYMENT VIEWSETS
# ============================================

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        payment_method = serializer.save(user=self.request.user)
        
        if payment_method.is_default:
            PaymentMethod.objects.filter(user=self.request.user).exclude(
                id=payment_method.id
            ).update(is_default=False)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).order_by('-created_at')


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause subscription"""
        subscription = self.get_object()
        pause_until = request.data.get('pause_until')
        
        subscription.status = 'paused'
        subscription.save()
        
        return Response({'status': 'paused', 'resumes_on': pause_until})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        
        subscription.status = 'canceled'
        subscription.auto_renew = False
        subscription.save()
        
        return Response({
            'status': 'canceled',
            'active_until': subscription.current_period_end
        })


# ============================================
# LESSON VIEWSET
# ============================================
"""
class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    queryset = Lesson.objects.all().order_by('-created_at')
"""

# ============================================
# CHAT VIEWSETS
# ============================================

class ChatThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatThread.objects.filter(
            participants=self.request.user
        ).order_by('-updated_at')


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        thread_id = self.request.query_params.get('thread_id')
        if not thread_id:
            return ChatMessage.objects.none()
        
        return ChatMessage.objects.filter(
            thread_id=thread_id
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        thread_id = self.request.data.get('thread_id')
        thread = ChatThread.objects.get(id=thread_id)
        
        receiver = thread.participants.exclude(id=self.request.user.id).first()
        
        message = serializer.save(
            sender=self.request.user,
            reciever=receiver,
            thread_id=thread_id
        )
        
        if 'attachment' in self.request.FILES:
            ChatAttachment.objects.create(
                message=message,
                file=self.request.FILES['attachment']
            )
    
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        if message.reciever == request.user:
            message.read_at = timezone.now()
            message.save()
        
        return Response({'read': True})
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.exceptions import ValidationError

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        thread_id = self.request.query_params.get('thread_id')
        if not thread_id:
            return ChatMessage.objects.none()
        return ChatMessage.objects.filter(thread_id=thread_id).order_by('created_at')

    @action(detail=False, methods=['post'])
    def new(self, request):
        """
        Create (send) a new chat message
        """
        thread_id = request.data.get('thread_id')
        text = request.data.get('text', '')

        if not thread_id:
            raise ValidationError("thread_id is required.")

        try:
            thread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            raise ValidationError("Thread not found.")

        receiver = thread.participants.exclude(id=request.user.id).first()
        if not receiver:
            raise ValidationError("No valid receiver found in thread.")

        # Create message
        message = ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            reciever=receiver,
            text=text,
        )

        # Handle attachments (single or multiple)
        for f in request.FILES.getlist('attachments'):
            ChatAttachment.objects.create(message=message, file=f)

        serializer = ChatMessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================
# WISHLIST VIEWSET
# ============================================
"""
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def purchase(self, request, pk=None):
      
        item = self.get_object()
        item.is_purchased = True
        item.purchased_on = request.data.get('purchased_on', date.today())
        item.save()
        
        return Response({'is_purchased': True})
"""

# ============================================
# FILE VIEWSET
# ============================================

"""class UserFileViewSet(viewsets.ModelViewSet):
    serializer_class = UserFileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserFile.objects.filter(user=self.request.user)
        tag = self.request.query_params.get('tag', None)
        
        if tag:
            queryset = queryset.filter(tag=tag)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)"""

# ============================================
# ANALYTICS VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_analytics(request):
    """Get weekly analytics"""
    week_start_param = request.query_params.get('week_start')
    if week_start_param:
        week_start = datetime.strptime(week_start_param, '%Y-%m-%d').date()
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    user = request.user
    
    daily_breakdown = []
    total_calories = total_protein = total_steps = workouts_completed = 0
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        
        food_entries = FoodDiaryEntry.objects.filter(user=user, date=day)
        day_calories = sum([
            (entry.food.calories if entry.food else entry.meal.calories) * entry.servings
            for entry in food_entries
        ])
        total_calories += day_calories
        
        day_protein = sum([
            (entry.food.protein if entry.food else entry.meal.protein) * entry.servings
            for entry in food_entries
        ])
        total_protein += day_protein
        
        activity = DailyActivitySummary.objects.filter(user=user, date=day).first()
        day_steps = activity.steps if activity else 0
        total_steps += day_steps
        
        workout = UserWorkoutLog.objects.filter(user=user, date=day, completed=True).exists()
        if workout:
            workouts_completed += 1
        
        daily_breakdown.append({
            'date': day,
            'calories': round(day_calories),
            'protein': round(day_protein),
            'steps': day_steps,
            'workout_completed': workout
        })
    
    progress_start = Progress.objects.filter(user=user, date__lte=week_start).order_by('-date').first()
    progress_end = Progress.objects.filter(user=user, date__lte=week_end).order_by('-date').first()
    
    weight_change = 0
    if progress_start and progress_end:
        weight_change = float(progress_end.weight) - float(progress_start.weight)
    
    return Response({
        'week_start': week_start,
        'week_end': week_end,
        'summary': {
            'weight_change': round(weight_change, 1),
            'avg_calories': round(total_calories / 7),
            'avg_protein': round(total_protein / 7),
            'avg_steps': round(total_steps / 7),
            'workouts_completed': workouts_completed,
            'workouts_target': user.profile.workouts_per_week
        },
        'daily_breakdown': daily_breakdown
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_analytics(request):
    """Get monthly analytics"""
    month_param = request.query_params.get('month')
    if month_param:
        year, month = map(int, month_param.split('-'))
        month_start = date(year, month, 1)
    else:
        today = date.today()
        month_start = date(today.year, today.month, 1)
    
    if month_start.month == 12:
        month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    
    user = request.user
    
    progress_start = Progress.objects.filter(user=user, date__lte=month_start).order_by('-date').first()
    progress_end = Progress.objects.filter(user=user, date__lte=month_end).order_by('-date').first()
    
    weight_start = float(progress_start.weight) if progress_start else 0
    weight_end = float(progress_end.weight) if progress_end else 0
    weight_change = weight_end - weight_start
    
    bf_change = 0
    if progress_start and progress_end and progress_start.body_fat_percentage and progress_end.body_fat_percentage:
        bf_change = float(progress_end.body_fat_percentage) - float(progress_start.body_fat_percentage)
    
    total_workouts = UserWorkoutLog.objects.filter(
        user=user, date__gte=month_start, date__lte=month_end, completed=True
    ).count()
    
    cardio_sessions = CardioSession.objects.filter(
        user=user, started_at__date__gte=month_start, started_at__date__lte=month_end
    )
    total_cardio = cardio_sessions.count()
    total_distance = cardio_sessions.aggregate(Sum('distance_m'))['distance_m__sum'] or 0
    
    food_entries = FoodDiaryEntry.objects.filter(
        user=user, date__gte=month_start, date__lte=month_end
    )
    
    days = (month_end - month_start).days + 1
    total_calories = sum([
        (entry.food.calories if entry.food else entry.meal.calories) * entry.servings
        for entry in food_entries
    ])
    avg_calories = round(total_calories / days) if days > 0 else 0
    
    return Response({
        'month': f"{month_start.year}-{month_start.month:02d}",
        'summary': {
            'weight_start': weight_start,
            'weight_end': weight_end,
            'weight_change': round(weight_change, 1),
            'body_fat_change': round(bf_change, 1),
            'total_workouts': total_workouts,
            'total_cardio_sessions': total_cardio,
            'total_distance_km': round(total_distance / 1000, 1),
            'avg_calories': avg_calories
        }
    })


# ============================================
# ADDITIONAL UTILITY VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Get overall user statistics"""
    user = request.user
    
    total_workouts = UserWorkoutLog.objects.filter(user=user, completed=True).count()
    total_cardio = CardioSession.objects.filter(user=user, ended_at__isnull=False).count()
    total_distance = CardioSession.objects.filter(user=user).aggregate(
        Sum('distance_m'))['distance_m__sum'] or 0
    
    # Current streak
    today = date.today()
    streak = 0
    check_date = today
    
    while True:
        has_activity = (
            UserWorkoutLog.objects.filter(user=user, date=check_date, completed=True).exists() or
            CardioSession.objects.filter(user=user, started_at__date=check_date).exists()
        )
        if has_activity:
            streak += 1
            check_date = check_date - timedelta(days=1)
        else:
            break
    
    first_progress = Progress.objects.filter(user=user).order_by('date').first()
    latest_progress = Progress.objects.filter(user=user).order_by('-date').first()
    
    weight_change = 0
    if first_progress and latest_progress:
        weight_change = float(latest_progress.weight) - float(first_progress.weight)
    
    return Response({
        'total_workouts': total_workouts,
        'total_cardio_sessions': total_cardio,
        'total_distance_km': round(total_distance / 1000, 1),
        'current_streak_days': streak,
        'weight_change_kg': round(weight_change, 1),
        'member_since': user.date_joined.strftime('%Y-%m-%d')
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_push_token(request):
    """Register device for push notifications"""
    platform = request.data.get('platform')
    token = request.data.get('token')
    
    # TODO: Store token in DeviceToken model
    
    return Response({'registered': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_clients(request):
    """List clients for coach"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    status_filter = request.query_params.get('status', None)
    checkin_status = request.query_params.get('checkin_status', None)
    
    profiles = UserProfile.objects.all()
    
    if status_filter:
        profiles = profiles.filter(status=status_filter)
    if checkin_status:
        profiles = profiles.filter(checkin_status=checkin_status)
    
    clients = []
    for profile in profiles:
        user = profile.user
        clients.append({
            'id': user.id,
            'name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'status': profile.status,
            'checkin_status': profile.checkin_status,
            'last_communication': profile.last_communication,
            'program_start_date': profile.program_start_date,
            'current_weight': float(profile.weight),
            'goal_weight': float(profile.target_weight) if profile.target_weight else None
        })
    
    return Response({'clients': clients})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_detail(request, client_id):
    """Get client detail for coach"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=client_id)
        profile = user.profile
        
        checkins = Checkin.objects.filter(user=user).order_by('-date')[:5]
        progress = Progress.objects.filter(user=user).order_by('-date')[:10]
        workouts = Workout.objects.filter(user=user, date__gte=date.today(), completed=False).order_by('date')[:5]
        meals = FoodDiaryEntry.objects.filter(user=user).order_by('-date', '-time')[:10]
        
        return Response({
            'profile': UserProfileSerializer(profile).data,
            'recent_checkins': CheckinSerializer(checkins, many=True).data,
            'progress_chart': ProgressSerializer(progress, many=True).data,
            'upcoming_workouts': WorkoutSerializer(workouts, many=True).data,
            'recent_meals': FoodDiaryEntrySerializer(meals, many=True).data
        })
    except User.DoesNotExist:
        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_workout_to_client(request, client_id):
    """Assign workout to client"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=client_id)
        workout_id = request.data.get('workout_id')
        workout_date = request.data.get('date')
        notes = request.data.get('notes', '')
        
        workout = Workout.objects.get(id=workout_id)
        
        new_workout = Workout.objects.create(
            user=user,
            name=workout.name,
            description=f"{workout.description}\n\nCoach Notes: {notes}",
            duration=workout.duration,
            level=workout.level,
            calories_burned=workout.calories_burned,
            date=workout_date,
            completed=False
        )
        
        for item in workout.items.all():
            WorkoutExercise.objects.create(
                workout=new_workout,
                exercise=item.exercise,
                order=item.order,
                sets=item.sets,
                reps=item.reps,
                reps_min=item.reps_min,
                reps_max=item.reps_max,
                rest_seconds=item.rest_seconds,
                notes=item.notes
            )
        
        return Response({'assigned': True})
    except (User.DoesNotExist, Workout.DoesNotExist):
        return Response({'error': 'User or workout not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_summary(request):
    """Get nutrition summary for date range"""
    from_date = request.query_params.get('from', date.today() - timedelta(days=7))
    to_date = request.query_params.get('to', date.today())
    
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    
    entries = FoodDiaryEntry.objects.filter(
        user=request.user,
        date__gte=from_date,
        date__lte=to_date
    )
    
    total_calories = total_protein = total_carbs = total_fats = 0
    
    for entry in entries:
        if entry.food:
            total_calories += entry.food.calories * entry.servings
            total_protein += entry.food.protein * entry.servings
            total_carbs += entry.food.carbs * entry.servings
            total_fats += entry.food.fat * entry.servings
        elif entry.meal:
            total_calories += entry.meal.calories * entry.servings
            total_protein += entry.meal.protein * entry.servings
            total_carbs += entry.meal.carbs * entry.servings
            total_fats += entry.meal.fats * entry.servings
    
    days = (to_date - from_date).days + 1
    
    return Response({
        'from_date': from_date,
        'to_date': to_date,
        'total_calories': round(total_calories),
        'total_protein': round(total_protein, 1),
        'total_carbs': round(total_carbs, 1),
        'total_fats': round(total_fats, 1),
        'avg_daily_calories': round(total_calories / days) if days > 0 else 0,
        'avg_daily_protein': round(total_protein / days, 1) if days > 0 else 0
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_log_water(request):
    """Quick log water with preset amounts"""
    preset = request.data.get('preset', '250')
    
    amount_map = {'250': 250, '500': 500, '750': 750, '1000': 1000}
    amount_ml = amount_map.get(preset, 250)
    
    WaterLog.objects.create(
        user=request.user,
        date=date.today(),
        amount_ml=amount_ml
    )
    
    total_today = WaterLog.objects.filter(
        user=request.user,
        date=date.today()
    ).aggregate(Sum('amount_ml'))['amount_ml__sum'] or 0
    
    goal = request.user.profile.daily_water_goal_ml
    
    return Response({
        'logged': True,
        'amount_ml': amount_ml,
        'total_today': total_today,
        'goal': goal,
        'remaining': max(0, goal - total_today),
        'percentage': round((total_today / goal) * 100, 1) if goal else 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exercise_personal_records(request):
    """Get all personal records for user"""
    user = request.user
    
    logged_exercises = SetLog.objects.filter(
        session__user=user,
        completed=True
    ).values_list('exercise_id', flat=True).distinct()
    
    prs = []
    
    for exercise_id in logged_exercises:
        exercise = Exercise.objects.get(id=exercise_id)
        
        max_weight_log = SetLog.objects.filter(
            session__user=user,
            exercise_id=exercise_id,
            completed=True,
            weight_kg__isnull=False
        ).order_by('-weight_kg').first()
        
        max_reps_log = SetLog.objects.filter(
            session__user=user,
            exercise_id=exercise_id,
            completed=True,
            reps__isnull=False
        ).order_by('-reps').first()
        
        pr_data = {
            'exercise_id': exercise_id,
            'exercise_name': exercise.name,
            'max_weight_kg': float(max_weight_log.weight_kg) if max_weight_log else None,
            'max_weight_date': str(max_weight_log.session.date) if max_weight_log else None,
            'max_reps': max_reps_log.reps if max_reps_log else None,
            'max_reps_weight': float(max_reps_log.weight_kg) if max_reps_log and max_reps_log.weight_kg else None
        }
        
        prs.append(pr_data)
    
    return Response({'personal_records': prs})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def muscle_group_volume(request):
    """Get training volume by muscle group for date range"""
    from_date = request.query_params.get('from', date.today() - timedelta(days=30))
    to_date = request.query_params.get('to', date.today())
    
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    
    sets = SetLog.objects.filter(
        session__user=request.user,
        session__date__gte=from_date,
        session__date__lte=to_date,
        completed=True
    ).select_related('exercise__primary_muscle')
    
    volume_by_group = {}
    
    for set_log in sets:
        if not set_log.exercise.primary_muscle:
            continue
            
        group = set_log.exercise.primary_muscle.group
        
        if group not in volume_by_group:
            volume_by_group[group] = {'total_sets': 0, 'total_volume_kg': 0}
        
        volume_by_group[group]['total_sets'] += 1
        
        if set_log.weight_kg and set_log.reps:
            volume_by_group[group]['total_volume_kg'] += float(set_log.weight_kg) * set_log.reps
    
    return Response({
        'from_date': from_date,
        'to_date': to_date,
        'volume_by_muscle_group': volume_by_group
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_workout(request, workout_id):
    """Duplicate a workout for a new date"""
    try:
        original = Workout.objects.get(id=workout_id, user=request.user)
        new_date = request.data.get('date', date.today())
        
        new_workout = Workout.objects.create(
            user=request.user,
            name=f"{original.name} (Copy)",
            description=original.description,
            duration=original.duration,
            level=original.level,
            calories_burned=original.calories_burned,
            date=new_date,
            completed=False
        )
        
        for item in original.items.all():
            WorkoutExercise.objects.create(
                workout=new_workout,
                exercise=item.exercise,
                order=item.order,
                sets=item.sets,
                reps=item.reps,
                reps_min=item.reps_min,
                reps_max=item.reps_max,
                rest_seconds=item.rest_seconds,
                notes=item.notes
            )
        
        serializer = WorkoutSerializer(new_workout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Workout.DoesNotExist:
        return Response({'error': 'Workout not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_calendar(request):
    """Get workout calendar for month"""
    month_param = request.query_params.get('month')
    if month_param:
        year, month = map(int, month_param.split('-'))
        month_start = date(year, month, 1)
    else:
        today = date.today()
        month_start = date(today.year, today.month, 1)
    
    if month_start.month == 12:
        month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    
    workout_logs = UserWorkoutLog.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=month_end
    ).select_related('workout')
    
    cardio_sessions = CardioSession.objects.filter(
        user=request.user,
        started_at__date__gte=month_start,
        started_at__date__lte=month_end
    )
    
    calendar = {}
    current_date = month_start
    
    while current_date <= month_end:
        date_str = str(current_date)
        
        day_workouts = workout_logs.filter(date=current_date)
        day_cardio = cardio_sessions.filter(started_at__date=current_date)
        
        calendar[date_str] = {
            'date': current_date,
            'has_workout': day_workouts.exists(),
            'workout_completed': day_workouts.filter(completed=True).exists(),
            'has_cardio': day_cardio.exists(),
            'total_activities': day_workouts.count() + day_cardio.count()
        }
        
        current_date += timedelta(days=1)
    
    return Response({
        'month': f"{month_start.year}-{month_start.month:02d}",
        'calendar': calendar
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meal_prep_list(request):
    """Get meal prep list for the week"""
    week_start = request.query_params.get('week_start')
    if week_start:
        week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    try:
        subscription = MealSubscription.objects.get(user=request.user, status='active')
        
        selections = WeeklyMealSelection.objects.filter(
            subscription=subscription,
            week_start=week_start
        ).select_related('meal')
        
        meals = []
        total_items = 0
        
        for selection in selections:
            meals.append({
                'meal_id': selection.meal.id,
                'meal_name': selection.meal.name,
                'quantity': selection.quantity,
                'calories': selection.meal.calories,
                'protein': selection.meal.protein
            })
            total_items += selection.quantity
        
        return Response({
            'week_start': week_start,
            'week_end': week_end,
            'total_meals': total_items,
            'meals': meals
        })
        
    except MealSubscription.DoesNotExist:
        return Response({
            'message': 'No active meal subscription',
            'week_start': week_start,
            'meals': []
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_food(request):
    """Create custom food item"""
    food = Food.objects.create(
        name=request.data['name'],
        is_custom=True,
        created_by=request.user,
        calories=request.data['calories'],
        protein=request.data['protein'],
        carbs=request.data['carbs'],
        fat=request.data['fats'],
        fiber=request.data.get('fiber', 0)
    )
    
    FoodPortion.objects.create(
        food=food,
        name="100 g",
        unit=ServingUnit.GRAM,
        quantity=100,
        grams=100
    )
    
    return Response(FoodSerializer(food).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compare_progress_dates(request):
    """Compare progress between two dates"""
    date1 = request.query_params.get('date1')
    date2 = request.query_params.get('date2')
    
    if not date1 or not date2:
        return Response({'error': 'Both date1 and date2 required'}, status=status.HTTP_400_BAD_REQUEST)
    
    date1 = datetime.strptime(date1, '%Y-%m-%d').date()
    date2 = datetime.strptime(date2, '%Y-%m-%d').date()
    
    progress1 = Progress.objects.filter(user=request.user, date__lte=date1).order_by('-date').first()
    progress2 = Progress.objects.filter(user=request.user, date__lte=date2).order_by('-date').first()
    
    if not progress1 or not progress2:
        return Response(
            {'error': 'Progress data not found for one or both dates'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    comparison = {
        'date1': progress1.date,
        'date2': progress2.date,
        'weight_change': round(float(progress2.weight) - float(progress1.weight), 1),
        'progress1': ProgressSerializer(progress1).data,
        'progress2': ProgressSerializer(progress2).data
    }
    
    if progress1.body_fat_percentage and progress2.body_fat_percentage:
        comparison['body_fat_change'] = round(
            float(progress2.body_fat_percentage) - float(progress1.body_fat_percentage), 1
        )
    
    if progress1.muscle_mass and progress2.muscle_mass:
        comparison['muscle_mass_change'] = round(
            float(progress2.muscle_mass) - float(progress1.muscle_mass), 1
        )
    
    return Response(comparison)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def share_recipe(request, recipe_id):
    """Share a recipe (make it public)"""
    try:
        recipe = Recipe.objects.get(id=recipe_id, created_by=request.user)
        recipe.is_public = True
        recipe.save()
        
        return Response({'message': 'Recipe shared successfully', 'is_public': True})
    except Recipe.DoesNotExist:
        return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copy_recipe(request, recipe_id):
    """Copy a public recipe to user's recipes"""
    try:
        original = Recipe.objects.get(id=recipe_id, is_public=True)
        
        new_recipe = Recipe.objects.create(
            name=f"{original.name} (Copy)",
            created_by=request.user,
            is_public=False,
            image=original.image
        )
        
        for ingredient in original.ingredients.all():
            RecipeIngredient.objects.create(
                recipe=new_recipe,
                food=ingredient.food,
                grams=ingredient.grams
            )
        
        serializer = RecipeSerializer(new_recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Recipe.DoesNotExist:
        return Response(
            {'error': 'Recipe not found or not public'},
            status=status.HTTP_404_NOT_FOUND
        )


class LessonViewSet(viewsets.ModelViewSet):
    """CRUD for lessons."""
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class WishlistViewSet(viewsets.ModelViewSet):
    """User's wishlist — linked to lessons."""
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserFileViewSet(viewsets.ModelViewSet):
    """Handle user file uploads."""
    serializer_class = UserFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Get user's cart with all items and totals"""
    try:
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        items = []
        subtotal = Decimal('0.00')
        
        for item in cart.items.select_related('meal'):
            item_total = item.meal.price * item.quantity
            subtotal += item_total
            
            items.append({
                'id': item.id,
                'meal_id': item.meal.id,
                'name': item.meal.name,
                'description': item.meal.description,
                'calories': item.meal.calories,
                'protein': f"{item.meal.protein}g",
                'quantity': item.quantity,
                'price_per_item': float(item.meal.price),
                'total_price': float(item_total),
                'image': request.build_absolute_uri(item.meal.image.url) if item.meal.image else None
            })
        
        # Calculate discount (10% example)
        discount_percentage = 10
        discount = subtotal * Decimal(discount_percentage) / 100
        delivery_fee = Decimal('0.00')  # Free delivery
        total = subtotal - discount + delivery_fee
        
        return Response({
            'success': True,
            'data': {
                'items': items,
                'subtotal': float(subtotal),
                'discount': float(discount),
                'discount_percentage': discount_percentage,
                'delivery_fee': float(delivery_fee),
                'total': float(total),
                'currency': 'Rs.',
                'item_count': len(items)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error fetching cart',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add meal to cart"""
    try:
        meal_id = request.data.get('food_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not meal_id:
            return Response({
                'success': False,
                'message': 'meal_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        meal = get_object_or_404(Food, id=meal_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            meal=meal,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'success': True,
            'message': 'Meal added to cart',
            'data': {
                'cart_item_id': cart_item.id,
                'quantity': cart_item.quantity,
                'total_items': cart.total_items
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error adding to cart',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response({
                'success': False,
                'message': 'Quantity is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = int(quantity)
        
        if quantity < 0:
            return Response({
                'success': False,
                'message': 'Quantity cannot be negative'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if quantity == 0:
            cart_item.delete()
            message = 'Item removed from cart'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Quantity updated successfully'
        
        # Recalculate total
        cart = Cart.objects.get(user=request.user)
        updated_total = cart.subtotal
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'item_id': item_id,
                'quantity': quantity if quantity > 0 else 0,
                'updated_total': float(updated_total)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error updating cart item',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        cart = Cart.objects.get(user=request.user)
        updated_total = cart.subtotal
        
        return Response({
            'success': True,
            'message': 'Item removed from cart successfully',
            'data': {
                'item_id': item_id,
                'updated_total': float(updated_total)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error removing cart item',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        
        return Response({
            'success': True,
            'message': 'Cart cleared successfully'
        }, status=status.HTTP_200_OK)
        
    except Cart.DoesNotExist:
        return Response({
            'success': True,
            'message': 'Cart is already empty'
        }, status=status.HTTP_200_OK)


# ============================================
# 2. ADDRESS MANAGEMENT (Already exists but add these helpers)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_addresses(request):
    """Get user's saved addresses"""
    try:
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        
        address_list = [{
            'id': addr.id,
            'full_name': addr.full_name,
            'phone': addr.phone,
            'street_address': f"{addr.line1} {addr.line2}".strip(),
            'city': addr.city,
            'province': addr.province,
            'postal_code': addr.postal_code,
            'is_default': addr.is_default
        } for addr in addresses]
        
        return Response({
            'success': True,
            'data': {
                'addresses': address_list
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error fetching addresses',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_shipping(request):
    """Validate shipping details"""
    try:
        full_name = request.data.get('full_name', '').strip()
        phone_number = request.data.get('phone_number', '').strip()
        street_address = request.data.get('street_address', '').strip()
        city = request.data.get('city', '').strip()
        province = request.data.get('province', '').strip()
        
        errors = []
        
        if not full_name or len(full_name) < 2:
            errors.append('Full name is required')
        
        if not phone_number or len(phone_number) < 10:
            errors.append('Valid phone number is required')
        
        if not street_address or len(street_address) < 5:
            errors.append('Street address is required')
        
        if not city:
            errors.append('City is required')
        
        if not province:
            errors.append('Province is required')
        
        if errors:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Shipping details validated successfully',
            'data': {
                'is_valid': True,
                'estimated_delivery': '8:00 AM - 9:00 AM'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error validating shipping details',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# 3. PAYMENT METHODS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_methods(request):
    """Get available payment methods"""
    try:
        saved_cards = PaymentMethod.objects.filter(
            user=request.user,
            provider='card'
        ).order_by('-is_default', '-created_at')
        
        cards_data = [{
            'id': card.id,
            'last4': card.last4,
            'brand': card.brand,
            'is_default': card.is_default
        } for card in saved_cards]
        
        payment_methods = [
            {
                'id': 'pm_card',
                'type': 'card',
                'name': 'Credit/Debit Card',
                'icon': 'credit_card',
                'enabled': True,
                'saved_cards': cards_data
            },
            {
                'id': 'pm_bank',
                'type': 'bank_transfer',
                'name': 'Bank Transfer',
                'icon': 'bank',
                'enabled': True
            },
            {
                'id': 'pm_google',
                'type': 'google_pay',
                'name': 'Google Pay',
                'icon': 'google_pay',
                'enabled': True
            }
        ]
        
        return Response({
            'success': True,
            'data': {
                'payment_methods': payment_methods
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error fetching payment methods',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request):
    """Process payment"""
    try:
        payment_method_id = request.data.get('payment_method_id')
        card_number = request.data.get('card_number', '').replace(' ', '')
        card_holder_name = request.data.get('card_holder_name', '').strip()
        expiry_date = request.data.get('expiry_date', '').strip()
        cvv = request.data.get('cvv', '').strip()
        save_card = request.data.get('save_card', False)
        
        # Validate based on payment method
        if payment_method_id == 'pm_card':
            if not all([card_number, card_holder_name, expiry_date, cvv]):
                return Response({
                    'success': False,
                    'message': 'All card details are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Basic validation
            if not card_number.isdigit() or len(card_number) != 16:
                return Response({
                    'success': False,
                    'message': 'Invalid card number'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not cvv.isdigit() or len(cvv) not in [3, 4]:
                return Response({
                    'success': False,
                    'message': 'Invalid CVV'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save card if requested
            if save_card:
                PaymentMethod.objects.create(
                    user=request.user,
                    provider='card',
                    brand='Visa',  # Detect from card number
                    last4=card_number[-4:],
                    is_default=not PaymentMethod.objects.filter(user=request.user, provider='card').exists()
                )
        
        # Generate payment IDs (in production, integrate with payment gateway)
        payment_id = f"pay_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        transaction_id = f"txn_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        return Response({
            'success': True,
            'message': 'Payment processed successfully',
            'data': {
                'payment_id': payment_id,
                'status': 'completed',
                'transaction_id': transaction_id
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Payment processing failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    """Get user's orders"""
    try:
        status_filter = request.query_params.get('status')
        
        orders = Order.objects.filter(user=request.user)
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        orders = orders.order_by('-created_at')
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'items_count': order.items_count,
                'scheduled_date': str(order.scheduled_date) if order.scheduled_date else None,
                'created_at': order.created_at.isoformat(),
                'estimated_delivery': f"{order.estimated_delivery_start} - {order.estimated_delivery_end}" if order.estimated_delivery_start else None
            })
        
        return Response({
            'success': True,
            'data': {
                'orders': orders_data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error fetching orders',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_id):
    """Get order details"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        items = []
        for item in order.items.select_related('meal'):
            items.append({
                'meal_id': item.meal.id,
                'name': item.meal.name,
                'quantity': item.quantity,
                'price_per_item': float(item.price_per_item),
                'total_price': float(item.total_price),
                'image': request.build_absolute_uri(item.meal.image.url) if item.meal.image else None
            })
        
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
            'subtotal': float(order.subtotal),
            'discount': float(order.discount),
            'delivery_fee': float(order.delivery_fee),
            'total_amount': float(order.total_amount),
            'shipping_name': order.shipping_name,
            'shipping_phone': order.shipping_phone,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'shipping_province': order.shipping_province,
            'scheduled_date': str(order.scheduled_date) if order.scheduled_date else None,
            'estimated_delivery': f"{order.estimated_delivery_start} - {order.estimated_delivery_end}" if order.estimated_delivery_start else None,
            'created_at': order.created_at.isoformat(),
            'items': items,
            'items_count': len(items)
        }
        
        return Response({
            'success': True,
            'data': order_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error fetching order details',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_or_update_meal_subscription(user, validated_data):
    """
    Handles the logic for Meal Section 2: Configuration and Preference Selection.
    """
    plan = validated_data['plan_id']
    address = validated_data['address_id']
    
    # Find an existing active subscription or create a new one
    subscription, created = MealSubscription.objects.get_or_create(
        user=user,
        status='active',
        defaults={
            'plan': plan,
            'address': address,
            'start_date': validated_data['start_date'],
            'meals_per_week': validated_data['meals_per_week'],
            'portion': validated_data['portion'],
            'protein_preference': validated_data['protein_preference'],
        }
    )

    if not created:
        # Update existing subscription with new preferences
        subscription.plan = plan
        subscription.address = address
        subscription.meals_per_week = validated_data['meals_per_week']
        subscription.portion = validated_data['portion']
        subscription.protein_preference = validated_data['protein_preference']
        subscription.start_date = validated_data['start_date']
        subscription.save()

    return subscription

def update_weekly_meal_selection(user, validated_data):
    """
    Handles the logic for Meal Section 3: Weekly Meal Selection.
    """
    subscription = validated_data['subscription_id']
    week_start = validated_data['week_start']
    meal = validated_data['meal_id']
    new_quantity = validated_data['quantity']

    if subscription.user != user:
        raise PermissionError("Subscription does not belong to the current user.")

    # 1. Get the current total meals selected for the week (excluding the meal being updated)
    current_total = WeeklyMealSelection.objects.filter(
        subscription=subscription,
        week_start=week_start
    ).exclude(meal=meal).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # 2. Calculate the new total
    new_total = current_total + new_quantity
    
    # 3. Check against the subscription limit
    if new_total > subscription.meals_per_week:
        raise ValueError(f"Total meals for the week ({new_total}) exceeds the subscription limit of {subscription.meals_per_week}.")

    if new_quantity == 0:
        # Remove the selection if quantity is 0
        WeeklyMealSelection.objects.filter(
            subscription=subscription,
            week_start=week_start,
            meal=meal
        ).delete()
        return None

    # 4. Create or update the selection
    selection, created = WeeklyMealSelection.objects.update_or_create(
        subscription=subscription,
        week_start=week_start,
        meal=meal,
        defaults={'quantity': new_quantity}
    )
    
    return selection
 
# --- API Views ---
from rest_framework.views import APIView
from django.db import transaction

class MealWorkflowView(APIView):
    """
    Handles the three main steps of the meal subscription and ordering workflow.
    """
    # NOTE: In a real Django app, you would add authentication/permission classes here

    def post(self, request, step):
        user = request.user # Assuming user is authenticated

        if step == 'configure':
            # Meal Section 2: Subscription Configuration
            serializer = SubscriptionInputSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                try:
                    subscription = create_or_update_meal_subscription(user, serializer.validated_data)
                    return Response(MealSubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)
                except (ValueError, PermissionError) as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif step == 'select_meals':
            # Meal Section 3: Weekly Meal Selection
            serializer = WeeklySelectionInputSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                try:
                    update_weekly_meal_selection(user, serializer.validated_data)
                    return Response({'detail': 'Meal selection updated successfully.'}, status=status.HTTP_200_OK)
                except (ValueError, PermissionError) as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif step == 'checkout':
            # Meal Sections 4-7: Final Checkout
            serializer = CheckoutInputSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                try:
                    order = create_final_order(user, serializer.validated_data)
                    return Response(MealOrderSerializer(order).data, status=status.HTTP_201_CREATED)
                except (ValueError, PermissionError, Exception) as e:
                    # Catch the generic Exception for payment failure
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Invalid workflow step.'}, status=status.HTTP_400_BAD_REQUEST)
def create_final_order(user, validated_data):
    """
    Handles the logic for Meal Sections 4, 5, 6, and 7: Checkout and Order Creation.
    """
    subscription = validated_data['subscription_id']
    week_start = validated_data['week_start']
    shipping_details = validated_data['shipping_details']
    payment_details = validated_data['payment_details']

    if subscription.user != user:
        raise PermissionError("Subscription does not belong to the current user.")

    # 1. Get the weekly meal selections
    selections = WeeklyMealSelection.objects.filter(
        subscription=subscription,
        week_start=week_start
    )
    if not selections.exists():
        raise ValueError("No meals selected for the specified week.")

    # 2. Calculate pricing and create OrderItems data
    subtotal = Decimal('0.00')
    order_items_data = []
    for selection in selections:
        price_per_item = selection.meal.price
        total_price = price_per_item * selection.quantity
        subtotal += total_price
        order_items_data.append({
            'meal': selection.meal,
            'quantity': selection.quantity,
            'price_per_item': price_per_item,
            'total_price': total_price
        })

    # 3. Apply mock discount and delivery fee
    DISCOUNT_RATE = Decimal('0.10')
    discount = subtotal * DISCOUNT_RATE
    delivery_fee = Decimal('0.00')
    total_amount = subtotal - discount + delivery_fee

    # 4. Mock Payment Processing
    # In a real app, this would be a call to a payment gateway
    payment_successful = True
    if not payment_successful:
        # Rollback the transaction if payment fails
        raise Exception("Payment failed. Please try again.")

    # 5. Create the Order object within a transaction
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            
            # Shipping Details
            shipping_name=shipping_details['full_name'],
            shipping_phone=shipping_details['phone'],
            shipping_address=shipping_details['street_address'],
            shipping_city=shipping_details['city'],
            shipping_province=shipping_details['province'],
            shipping_postal_code=shipping_details.get('postal_code', ''),
            
            # Payment Details
            payment_method=payment_details['method'],
            payment_status=Order.PAYMENT_STATUS[2][0], # 'completed'
            
            # Delivery
            status=Order.STATUS_CHOICES[1][0], # 'confirmed'
            scheduled_date=week_start
        )

        # 6. Create OrderItem objects
        order_items = [MealOrderItem(order=order, **data) for data in order_items_data]
        MealOrderItem.objects.bulk_create(order_items)

        # 7. Clean up selections (optional: remove selections after order is placed)
        # selections.delete()

    return order