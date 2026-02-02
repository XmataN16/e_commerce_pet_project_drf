# accounts/models.py
import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role_annotation = models.CharField(max_length=64, blank=True, null=True)  # optional
    is_active = models.BooleanField(default=True)  # soft delete (override AbstractUser default if needed)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email}"

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. 'seller'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)  # e.g. 'product.create'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    perm = models.ForeignKey(Permission, on_delete=models.CASCADE)
    # optional: allow_own flag vs allow_all? We'll encode as two perms (e.g. 'order.read_own' vs 'order.read_all')

    class Meta:
        unique_together = ("role", "perm")

class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="users")

    class Meta:
        unique_together = ("user", "role")

# --- token storage ---
class RefreshToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=128, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    ip = models.CharField(max_length=64, blank=True, null=True)  # optional
    user_agent = models.TextField(blank=True, null=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    @staticmethod
    def hash_token(raw_token: str) -> str:
        # store SHA256 hex digest
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def check_token(self, raw_token: str) -> bool:
        return self.token_hash == self.hash_token(raw_token)

class JWTBlacklist(models.Model):
    jti = models.CharField(max_length=200, unique=True, db_index=True)
    reason = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
