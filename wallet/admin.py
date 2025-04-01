from django.contrib import admin
from .models import UserWallet

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient_id', 'created_at')
