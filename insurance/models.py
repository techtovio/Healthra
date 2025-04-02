from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class InsurancePlan(models.Model):
    PLAN_TYPES = [
        ('BASIC', 'Basic Coverage'),
        ('STANDARD', 'Standard Coverage'),
        ('PREMIUM', 'Premium Coverage'),
        ('SENIOR', 'Senior Care Plan'),
        ('STUDENT', 'Affordable coverage for students with basic needs')
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    description = models.TextField()
    monthly_cost_hbar = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    annual_discount = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount percentage for annual payment"
    )
    coverage_details = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.monthly_cost_hbar} HBAR/month"

class UserInsurance(models.Model):
    PAYMENT_FREQUENCY = [
        ('MONTHLY', 'Monthly'),
        ('ANNUAL', 'Annual'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending Payment'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insurances')
    plan = models.ForeignKey(InsurancePlan, on_delete=models.PROTECT)
    payment_frequency = models.CharField(max_length=10, choices=PAYMENT_FREQUENCY)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    hbar_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} Insurance"

class InsurancePayment(models.Model):
    insurance = models.ForeignKey(UserInsurance, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount_hbar = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    coverage_period_start = models.DateField()
    coverage_period_end = models.DateField()
    is_successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.insurance} - {self.amount_hbar} HBAR"