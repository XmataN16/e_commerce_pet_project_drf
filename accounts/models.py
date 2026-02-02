from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # роли: admin(superuser), seller, customer, support
    ROLE_CHOICES = (
        ("seller", "Seller"),
        ("customer", "Customer"),
        ("support", "Support"),
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, null=True, blank=True)

    phone_number = models.CharField(max_length=32, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # soft delete flag

    def __str__(self):
        return f"{self.username} ({self.role})"
