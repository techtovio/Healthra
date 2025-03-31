from django.urls import path
from .views import TransactionListView, CreateTransactionView, LiquidityPoolView

urlpatterns = [
    path('transactions/', TransactionListView.as_view(), name='transactions'),
    path('transactions/create/', CreateTransactionView.as_view(), name='create-transaction'),
    path('liquidity/', LiquidityPoolView.as_view(), name='liquidity-pool'),
]