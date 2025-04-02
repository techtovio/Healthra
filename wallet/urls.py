from django.urls import path
from wallet import views

urlpatterns = [
    path('wallet/details/', views.wallet_details, name='wallet-details'),
    path('wallet/balance/', views.wallet_balance, name='wallet-balance'),
    path('wallet/transfer/', views.fund_claim, name='wallet-transfer'),
    path('wallet/history/', views.transaction_history, name='wallet-history'),
    path('wallet/buy-hlt/', views.buy_hlt, name='buy_hlt'),
    path('api/token-info/', views.token_info, name='token_info'),
    path('api/account-balance/', views.wallet_balance, name='account_balance'),
    path('api/token-holders/', views.token_holders, name='token_holders'),
    path('user/transactions/', views.wallet_history, name='wallet_history')
]