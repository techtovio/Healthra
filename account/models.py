from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
import string
import random
from datetime import datetime, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from cryptography.fernet import Fernet
from django.db.models import Sum, Count, Avg
from datetime import datetime
from django.utils.timezone import now
from django.db.models import Count, F, Q, Sum

# Generate or retrieve your encryption key safely in the settings file
from django.conf import settings

def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

MEANS_OF_PAYMENT = (
    ("Mpesa", "Mpesa"),
    ("Cash", "Cash"),
    ("Bank", "Bank")
)

TYPE_OF_PAYMENT = (
    ("Deposit", "Deposit"),
    ("Withdrawal", "Withdrawal"),
    ("Transfer", "Transfer")
)

STATUS_CHOICES = (
    ("Completed", "Completed"),
    ("Pending", "Pending"),
    ("Cancelled", "Cancelled")
)

class Verify(models.Model):
    phone_no = models.CharField(max_length=10, null=False, blank=False)
    code = models.CharField(max_length=13)
    attempts = models.PositiveIntegerField(default=5)
    times_Day = models.PositiveIntegerField(default=3)
    status = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_no
    

GENDER_CHOICES = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
    ('None', 'Prefer not to say')
)

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to="profile", blank=True, null=True)
    phone_no = models.CharField(max_length=10, unique=True)
    county = models.CharField(max_length=100, default="Nairobi")
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES, default="None")
    funds = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    is_verified = models.BooleanField(default=False)
    
    def notifications_count(self) -> int:
        """Returns the count of notifications for the user."""
        return self.user.notifications.filter(is_read=False).count()

    def name(self) -> str:
        return self.user.get_full_name()

    def account_age(self) -> int:
        """Calculate account age in months."""
        if self.user.date_joined:
            return (now() - self.user.date_joined).days // 30
        return 0
    
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_OF_PAYMENT, default="Deposit")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    reference = models.CharField(max_length=12)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)
    
    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.amount}"

    @classmethod
    def total_amount_by_type(cls, transaction_type):
        """
        Calculate the total amount for a given transaction type.
        """
        return cls.objects.filter(type=transaction_type, status="Completed").aggregate(total=Sum('amount'))['total'] or 0

    @classmethod
    def count_transactions_by_type(cls, transaction_type):
        """
        Count the number of transactions for a given type.
        """
        return cls.objects.filter(type=transaction_type).count()

    @classmethod
    def average_amount_by_type(cls, transaction_type):
        """
        Calculate the average transaction amount for a given type.
        """
        return cls.objects.filter(type=transaction_type, status="Completed").aggregate(average=Avg('amount'))['average'] or 0

    @classmethod
    def transaction_summary(cls):
        """
        Get a summary of all transaction types with their total amounts and counts.
        """
        summary = {}
        for transaction_type, _ in TYPE_OF_PAYMENT:
            summary[transaction_type] = {
                "total_amount": cls.total_amount_by_type(transaction_type),
                "count": cls.count_transactions_by_type(transaction_type),
                "average_amount": cls.average_amount_by_type(transaction_type)
            }
        return summary

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)
    
    def __str__(self):
        return self.user.email

def get_deadline():
    return datetime.now() + timedelta(days=30)

class Message(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return self.name