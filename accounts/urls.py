from django.urls import path
from .views import RegisterView, LoginView, ProtectedView, ProfileView, LogoutView, ChangePasswordView, \
    ResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
