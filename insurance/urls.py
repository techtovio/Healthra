from django.urls import path
from .views import HealthPlanListCreateView, ClaimListCreateView

urlpatterns = [
    path('plans/', HealthPlanListCreateView.as_view(), name='health-plans'),
    path('claims/', ClaimListCreateView.as_view(), name='claims'),
]