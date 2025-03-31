from django.db import models
import uuid

# Create your models here.
class Transaction(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, choices=[('HLT', 'Healthra Token'), ('Fiat', 'Fiat')])
    transaction_type = models.CharField(max_length=10, choices=[('Deposit', 'Deposit'), ('Withdrawal', 'Withdrawal'), ('Claim', 'Claim')])
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')], default='Pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.status}"
        

class LiquidityPool(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    total_hlt = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_fiat = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"HLT: {self.total_hlt} | Fiat: {self.total_fiat}"