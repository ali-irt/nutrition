import logging
from datetime import datetime
from django.contrib.auth.models import User
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.shortcuts import Http404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import *
from .serializers import *

logger = logging.getLogger(__name__)

# =====================================
# Helper for consistent logging context
# =====================================
def log_request_context(request, message=""):
    return (
        f"[{datetime.now()}] user={getattr(request.user, 'username', 'Anonymous')} "
        f"method={request.method} path={request.path} "
        f"ip={request.META.get('REMOTE_ADDR', 'Unknown')} {message}"
    )


# =====================================
# Auth
# =====================================
class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            logger.info(log_request_context(request, f"Login attempt username={request.data.get('username')}"))
            response = super().post(request, *args, **kwargs)
            logger.info(log_request_context(request, "Login successful"))
            return response
        except Exception as e:
            logger.error(log_request_context(request, f"Login failed: {e}"), exc_info=True)
            return Response({'error': 'Login failed due to server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def register_user(request):
    try:
        logger.info(log_request_context(request, "Registration attempt"))

        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([username, email, password]):
            logger.warning(log_request_context(request, "Missing required registration fields"))
            return Response({'error': 'Username, email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            logger.warning(log_request_context(request, f"Username already exists: {username}"))
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            logger.warning(log_request_context(request, f"Email already registered: {email}"))
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        refresh = RefreshToken.for_user(user)

        logger.info(log_request_context(request, f"User registered successfully username={username}"))
        return Response({
            'message': 'User registered successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(log_request_context(request, f"Registration failed: {e}"), exc_info=True)
        return Response({'error': 'Registration failed due to server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================
# Base ViewSet with standard logging
# =====================================
class LoggedModelViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        logger.info(log_request_context(request, f"Listing {self.__class__.__name__}"))
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(log_request_context(request, f"List failed: {e}"), exc_info=True)
            return Response({'error': 'List failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        logger.info(log_request_context(request, f"Retrieving {self.__class__.__name__}"))
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            logger.warning(log_request_context(request, "Retrieve failed: Not found"))
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(log_request_context(request, f"Retrieve failed: {e}"), exc_info=True)
            return Response({'error': 'Retrieve failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        logger.info(log_request_context(request, f"Creating {self.__class__.__name__}"))
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as ve:
            logger.warning(log_request_context(request, f"Validation error: {ve}"))
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(log_request_context(request, f"Create failed: {e}"), exc_info=True)
            return Response({'error': 'Create failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        logger.info(log_request_context(request, f"Updating {self.__class__.__name__}"))
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(log_request_context(request, f"Update failed: {e}"), exc_info=True)
            return Response({'error': 'Update failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        logger.info(log_request_context(request, f"Deleting {self.__class__.__name__}"))
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(log_request_context(request, f"Delete failed: {e}"), exc_info=True)
            return Response({'error': 'Delete failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================
# Actual ViewSets using the logging base
# =====================================
class WorkoutViewSet(LoggedModelViewSet):
    serializer_class = WorkoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching workouts"))
        return Workout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving new workout"))
        serializer.save(user=self.request.user)


class MealViewSet(LoggedModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer


class UserProfileViewSet(LoggedModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        user = self.request.user
        logger.debug(log_request_context(self.request, "Fetching user profiles"))
        return self.queryset if user.is_staff else self.queryset.filter(user=user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving new profile"))
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        try:
            logger.info(log_request_context(request, "Accessing 'me' profile endpoint"))
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            if created:
                logger.info(log_request_context(request, "Created new profile for current user"))

            if request.method in ('PUT', 'PATCH'):
                serializer = self.get_serializer(profile, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                logger.info(log_request_context(request, "Profile updated via 'me' endpoint"))
                return Response(serializer.data)

            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        except Exception as e:
            logger.error(log_request_context(request, f"Error in 'me' endpoint: {e}"), exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserWorkoutLogViewSet(LoggedModelViewSet):
    serializer_class = UserWorkoutLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching workout logs"))
        return UserWorkoutLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving workout log"))
        serializer.save(user=self.request.user)


class UserMealLogViewSet(LoggedModelViewSet):
    queryset = UserMealLog.objects.all()
    serializer_class = UserMealLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching meal logs"))
        return UserMealLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving meal log"))
        serializer.save(user=self.request.user)


class ProgressViewSet(LoggedModelViewSet):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching progress entries"))
        return Progress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving progress entry"))
        serializer.save(user=self.request.user)


class WishlistItemViewSet(LoggedModelViewSet):
    queryset = WishlistItem.objects.all()
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching wishlist items"))
        return WishlistItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving wishlist item"))
        serializer.save(user=self.request.user)


class MyAPIView(APIView):
    def get(self, request):
        try:
            logger.info(log_request_context(request, "GET request to MyAPIView"))
            return Response({"message": "OK"})
        except Exception as e:
            logger.error(log_request_context(request, f"MyAPIView error: {e}"), exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
