from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from .models import Transaction
from .serializers import TransactionSerializer

# List Transactions for a User
class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

# Create Transaction (Deposit, Withdrawal, Claim)
class CreateTransactionView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        
        
        
from rest_framework import generics, permissions
from .models import LiquidityPool
from .serializers import LiquidityPoolSerializer

# View Liquidity Pool
class LiquidityPoolView(generics.RetrieveAPIView):
    queryset = LiquidityPool.objects.all()
    serializer_class = LiquidityPoolSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return LiquidityPool.objects.first()