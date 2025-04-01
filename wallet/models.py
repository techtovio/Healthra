import os
from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import uuid
import base64
from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
    TokenAssociateTransaction,
)
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class UserWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    qpt_public_key = models.CharField(max_length=256, blank=True, null=True)
    qpt_private_key = models.CharField(max_length=256, blank=True, null=True, editable=False)
    recipient_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Encrypt private keys before saving."""
        if self.qpt_private_key:
            key_str = str(self.qpt_private_key)  # Ensure it's a string
            if not key_str.startswith("gAAAA"):  # Avoid double encryption
                self.qpt_private_key = self.encrypt_key(key_str)
        super().save(*args, **kwargs)

    def encrypt_key(self, key: str) -> str:
        """
        Encrypt the private key using Fernet.
        """
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            # Ensure the secret key is 32 bytes long
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.encrypt(key.encode()).decode()
        except Exception as e:
            raise ValueError(f"Encryption error: {e}")

    def decrypt_key(self) -> str:
        """
        Decrypt the private key using Fernet.
        """
        try:
            secret_key = os.getenv('SECRET_KEY')
            if not secret_key:
                raise ValueError("Missing SECRET_KEY in environment variables")
            
            # Ensure the secret key is 32 bytes long
            key_bytes = secret_key.encode()
            key_base64 = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            f = Fernet(key_base64)
            return f.decrypt(self.qpt_private_key.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption error: {e}")

    def __str__(self):
        return f"{self.user.username} Wallet"

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('SEND', 'Send'),
        ('RECEIVE', 'Receive'),
        ('WITHDRAW', 'Withdraw')
    ]
    
    CURRENCY_TYPE = [
        ('QPT', 'QPT'),
        ('HBAR', 'HBAR')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hashgraph')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    currency = models.CharField(max_length=10, choices=CURRENCY_TYPE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    recipient_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.currency}"