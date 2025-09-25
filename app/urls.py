from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import *

router = DefaultRouter()
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'profiles', UserProfileViewSet, basename='profile')  # This is correct
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'workout-logs', UserWorkoutLogViewSet, basename='workout-log')
router.register(r'meal-logs', UserMealLogViewSet, basename='meal-log')
router.register(r'progress', ProgressViewSet, basename='progress')
router.register(r'wishlist', WishlistItemViewSet, basename='wishlist-item')

urlpatterns = [
    path('auth/register/', register_user, name='register'),
    path('api/login/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    path('router/', include(router.urls)),
    path('auth/api-token-auth/', obtain_auth_token, name='api-token-auth'), 
]

# Optional DRF Spectacular documentation
try:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
    )
    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    ]
except ImportError:
    pass