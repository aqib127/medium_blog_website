from django.urls import path
from .views import (
    UserProfileView, UserStoriesView, FollowersView, FollowingView,
    FollowToggleView, ProfileUpdateView, AvatarUpdateView
)

urlpatterns = [
    path('<str:handle>/', UserProfileView.as_view(), name='user-profile'),
    path('<str:handle>/stories/', UserStoriesView.as_view(), name='user-stories'),
    path('<str:handle>/followers/', FollowersView.as_view(), name='user-followers'),
    path('<str:handle>/following/', FollowingView.as_view(), name='user-following'),
    path('<str:handle>/follow/', FollowToggleView.as_view(), name='user-follow'),
    path('<str:handle>/update/', ProfileUpdateView.as_view(), name='user-update'),
    path('<str:handle>/avatar/', AvatarUpdateView.as_view(), name='user-avatar'),
]