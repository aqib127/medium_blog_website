from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    RegisterView, LogoutView, MeView, CustomTokenObtainPairView,
    UserProfileView, UserStoriesView, FollowersView, FollowingView,
    FollowToggleView, ProfileUpdateView, AvatarUpdateView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),

    # NEW: User Profile and Interaction endpoints
    # Note: Using <str:handle> because your views use lookup_field='handle'
    path('<str:handle>/', UserProfileView.as_view(), name='user_profile'),
    path('<str:handle>/stories/', UserStoriesView.as_view(), name='user_stories'),
    path('<str:handle>/followers/', FollowersView.as_view(), name='user_followers'),
    path('<str:handle>/following/', FollowingView.as_view(), name='user_following'),
    path('<str:handle>/follow/', FollowToggleView.as_view(), name='user_follow_toggle'),
    path('<str:handle>/update/', ProfileUpdateView.as_view(), name='user_update'),
    path('<str:handle>/avatar/', AvatarUpdateView.as_view(), name='user_avatar'),
]