from django.urls import path
from wallet import views

urlpatterns = [
    path('wallet/details/', views.wallet_details, name='wallet-details'),
    path('wallet/balance/', views.wallet_balance, name='wallet-balance'),
    path('wallet/transfer/', views.fund_clubs, name='wallet-transfer'),
    path('wallet/history/', views.transaction_history, name='wallet-history'),
    path('wallet/asign-users/', views.fund_clubs, name='assign'),
    path('wallet/buy-qpt/', views.buy_qpt, name='buy_qpt'),
    path('api/token-info/', views.token_info, name='token_info'),
    path('api/account-balance/', views.account_balance, name='account_balance'),
    path('api/token-holders/', views.token_holders, name='token_holders'),
]