from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from .models import HealthPlan
from .serializers import HealthPlanSerializer

# List & Create Health Plans
class HealthPlanListCreateView(generics.ListCreateAPIView):
    queryset = HealthPlan.objects.all()
    serializer_class = HealthPlanSerializer
    permission_classes = [permissions.AllowAny]
    
from rest_framework import generics, permissions
from .models import Claim
from .serializers import ClaimSerializer

# List & Create Claims
class ClaimListCreateView(generics.ListCreateAPIView):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)