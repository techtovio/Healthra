from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    preferred_currency = models.CharField(max_length=10, choices=[('HLT', 'Healthra Token'), ('Fiat', 'Fiat')], default='HLT')
    
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # Unique related_name
        blank=True
    )
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True )

    def __str__(self):
        return self.username