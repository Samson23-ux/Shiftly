from rest_framework.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="Login Endpoint"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="Refresh token"),
]
