import views as AppViews
from rest_framework.routers import DefaultRouter
from rest_framework.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="Login Endpoint"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="Refresh token"),
    path(
        "shifts/<uuid:shift_id>/claims/",
        AppViews.ShiftClaimViewSet.as_view({"post": "create"}),
        name="Claim shift",
    ),
    path(
        "shifts/claims/",
        AppViews.ShiftClaimViewSet.as_view({"get": "list"}),
        name="Get shift claims",
    ),
    path(
        "shifts/claims/<uuid:claim_id>/",
        AppViews.ShiftClaimViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="Get a shift claim",
    ),
    path(
        "shifts/requests/",
        AppViews.SwapRequestViewSet.as_view({"get": "list"}),
        name="List swap requests",
    ),
    path(
        "shifts/requests/<uuid:swap_id>/accept/",
        AppViews.SwapRequestViewSet.as_view({"patch": "accept_swap_request"}),
        name="Accept swap request",
    ),
    path(
        "shifts/requests/<uuid:swap_id>/reject/",
        AppViews.SwapRequestViewSet.as_view({"patch": "reject_swap_request"}),
        name="Reject swap request",
    ),
    path(
        "shifts/requests/<uuid:swap_id>/approve/",
        AppViews.SwapRequestViewSet.as_view({"patch": "approve_swap_request"}),
        name="Approve swap request",
    ),
    path(
        "shifts/requests/<uuid:swap_id>/cancel/",
        AppViews.SwapRequestViewSet.as_view({"patch": "cancel_swap_request"}),
        name="Cancel swap request",
    ),
    path(
        "shifts/requests/<uuid:swap_id>/",
        AppViews.SwapRequestViewSet.as_view({"get": "retrieve"}),
        name="Get a swap request",
    ),
    path(
        "shifts/requests/swap/",
        AppViews.SwapRequestViewSet.as_view({"post": "create"}),
        name="Create swap request",
    ),
]


router = DefaultRouter()
router.register(r"employees", AppViews.EmployeeViewSet.as_view())
router.register(r"employees", AppViews.ShiftViewSet.as_view())

urlpatterns += router.urls
