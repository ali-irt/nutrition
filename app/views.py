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
# Add these ViewSets to your existing views.py file

# =====================================
# Nutrition ViewSet
# =====================================
class NutritionViewSet(LoggedModelViewSet):
    serializer_class = NutritionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching nutrition entries"))
        return Nutrition.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving nutrition entry"))
        serializer.save(user=self.request.user)


# =====================================
# Lead Management ViewSet
# =====================================
class LeadViewSet(LoggedModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching leads"))
        # Only staff can see all leads
        if self.request.user.is_staff:
            return Lead.objects.all()
        return Lead.objects.none()


# =====================================
# OTP ViewSet (Read-only for users)
# =====================================
class LoginOTPViewSet(LoggedModelViewSet):
    serializer_class = LoginOTPSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']  # Read-only

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching OTP records"))
        return LoginOTP.objects.filter(user=self.request.user)


# =====================================
# Macro Planning ViewSets
# =====================================
class MacroPlanViewSet(LoggedModelViewSet):
    serializer_class = MacroPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching macro plans"))
        return MacroPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving macro plan"))
        serializer.save(user=self.request.user)


class DailyMacroTargetViewSet(LoggedModelViewSet):
    serializer_class = DailyMacroTargetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching daily macro targets"))
        return DailyMacroTarget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving daily macro target"))
        serializer.save(user=self.request.user)


# =====================================
# Activity Tracking ViewSets
# =====================================
class WaterLogViewSet(LoggedModelViewSet):
    serializer_class = WaterLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching water logs"))
        return WaterLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving water log"))
        serializer.save(user=self.request.user)


class DailyActivitySummaryViewSet(LoggedModelViewSet):
    serializer_class = DailyActivitySummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching activity summaries"))
        return DailyActivitySummary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving activity summary"))
        serializer.save(user=self.request.user)


class HeartRateSampleViewSet(LoggedModelViewSet):
    serializer_class = HeartRateSampleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching heart rate samples"))
        return HeartRateSample.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving heart rate sample"))
        serializer.save(user=self.request.user)


# =====================================
# Check-in ViewSets
# =====================================
class CheckinFormViewSet(LoggedModelViewSet):
    queryset = CheckinForm.objects.all()
    serializer_class = CheckinFormSerializer
    permission_classes = [IsAuthenticated]


class CheckinQuestionViewSet(LoggedModelViewSet):
    queryset = CheckinQuestion.objects.all()
    serializer_class = CheckinQuestionSerializer
    permission_classes = [IsAuthenticated]


class CheckinViewSet(LoggedModelViewSet):
    serializer_class = CheckinSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching check-ins"))
        return Checkin.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving check-in"))
        serializer.save(user=self.request.user)


class CheckinAnswerViewSet(LoggedModelViewSet):
    serializer_class = CheckinAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching check-in answers"))
        return CheckinAnswer.objects.filter(checkin__user=self.request.user)


class CheckinPhotoViewSet(LoggedModelViewSet):
    serializer_class = CheckinPhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching check-in photos"))
        return CheckinPhoto.objects.filter(checkin__user=self.request.user)


# =====================================
# Food Library ViewSets
# =====================================
class FoodBrandViewSet(LoggedModelViewSet):
    queryset = FoodBrand.objects.all()
    serializer_class = FoodBrandSerializer
    permission_classes = [IsAuthenticated]


class FoodViewSet(LoggedModelViewSet):
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching foods"))
        # Show all non-custom foods + user's custom foods
        return Food.objects.filter(
            models.Q(is_custom=False) | models.Q(created_by=self.request.user)
        )

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving food"))
        serializer.save(created_by=self.request.user, is_custom=True)


class FoodBarcodeViewSet(LoggedModelViewSet):
    queryset = FoodBarcode.objects.all()
    serializer_class = FoodBarcodeSerializer
    permission_classes = [IsAuthenticated]


class FoodPortionViewSet(LoggedModelViewSet):
    queryset = FoodPortion.objects.all()
    serializer_class = FoodPortionSerializer
    permission_classes = [IsAuthenticated]


class RecipeViewSet(LoggedModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching recipes"))
        # Show public recipes + user's own recipes
        return Recipe.objects.filter(
            models.Q(is_public=True) | models.Q(created_by=self.request.user)
        )

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving recipe"))
        serializer.save(created_by=self.request.user)


class RecipeIngredientViewSet(LoggedModelViewSet):
    serializer_class = RecipeIngredientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching recipe ingredients"))
        return RecipeIngredient.objects.filter(
            models.Q(recipe__is_public=True) | models.Q(recipe__created_by=self.request.user)
        )


class FoodDiaryEntryViewSet(LoggedModelViewSet):
    serializer_class = FoodDiaryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching food diary entries"))
        return FoodDiaryEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving food diary entry"))
        serializer.save(user=self.request.user)


# =====================================
# Exercise Library ViewSets
# =====================================
class MuscleViewSet(LoggedModelViewSet):
    queryset = Muscle.objects.all()
    serializer_class = MuscleSerializer
    permission_classes = [IsAuthenticated]


class ExerciseViewSet(LoggedModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]


class WorkoutExerciseViewSet(LoggedModelViewSet):
    serializer_class = WorkoutExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching workout exercises"))
        return WorkoutExercise.objects.filter(workout__user=self.request.user)


class SetLogViewSet(LoggedModelViewSet):
    serializer_class = SetLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching set logs"))
        return SetLog.objects.filter(session__user=self.request.user)


# =====================================
# Cardio ViewSet
# =====================================
class CardioSessionViewSet(LoggedModelViewSet):
    serializer_class = CardioSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching cardio sessions"))
        return CardioSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving cardio session"))
        serializer.save(user=self.request.user)


# =====================================
# Address & Subscription ViewSets
# =====================================
class AddressViewSet(LoggedModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching addresses"))
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving address"))
        serializer.save(user=self.request.user)


class ProductViewSet(LoggedModelViewSet):
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class PlanViewSet(LoggedModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]


class SubscriptionViewSet(LoggedModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching subscriptions"))
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving subscription"))
        serializer.save(user=self.request.user)


class PaymentMethodViewSet(LoggedModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching payment methods"))
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving payment method"))
        serializer.save(user=self.request.user)


class InvoiceViewSet(LoggedModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching invoices"))
        return Invoice.objects.filter(user=self.request.user)


class PaymentViewSet(LoggedModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching payments"))
        return Payment.objects.filter(invoice__user=self.request.user)


# =====================================
# Meal Subscription ViewSets
# =====================================
class MealSubscriptionViewSet(LoggedModelViewSet):
    serializer_class = MealSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching meal subscriptions"))
        return MealSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving meal subscription"))
        serializer.save(user=self.request.user)


class WeeklyMealSelectionViewSet(LoggedModelViewSet):
    serializer_class = WeeklyMealSelectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching weekly meal selections"))
        return WeeklyMealSelection.objects.filter(subscription__user=self.request.user)


class DeliveryViewSet(LoggedModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching deliveries"))
        return Delivery.objects.filter(subscription__user=self.request.user)


# =====================================
# Chat & Files ViewSets
# =====================================
class ChatThreadViewSet(LoggedModelViewSet):
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching chat threads"))
        return ChatThread.objects.filter(participants=self.request.user)


class ChatMessageViewSet(LoggedModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching chat messages"))
        return ChatMessage.objects.filter(thread__participants=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving chat message"))
        serializer.save(sender=self.request.user)


class ChatAttachmentViewSet(LoggedModelViewSet):
    serializer_class = ChatAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching chat attachments"))
        return ChatAttachment.objects.filter(message__thread__participants=self.request.user)


class UserFileViewSet(LoggedModelViewSet):
    serializer_class = UserFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug(log_request_context(self.request, "Fetching user files"))
        return UserFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(log_request_context(self.request, "Saving user file"))
        serializer.save(user=self.request.user)


#_---------------------
#stripe workflow
#-----------------------


import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        currency = request.data.get("currency", "usd")

        # Create local payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=amount,
            currency=currency,
            status="pending",
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {
                                "name": "Revona Subscription / Service Payment",
                            },
                            "unit_amount": int(float(amount) * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
               success_url="http://127.0.0.1:8000/payment/success/",
cancel_url="http://127.0.0.1:8000/payment/cancel/",

                metadata={"payment_id": payment.id},
            )

            payment.stripe_session_id = checkout_session.id
            payment.save()

            return Response({"checkout_url": checkout_session.url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import stripe, json
from django.conf import settings
from .models import Payment, Subscription


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session["metadata"]["payment_id"]

        payment = get_object_or_404(Payment, id=payment_id)
        payment.status = "paid"
        payment.save()

        # Optional: auto-create subscription
        Subscription.objects.create(
            user=payment.user,
            plan_name="Premium Plan",
            is_active=True,
        )

    return HttpResponse(status=200)
