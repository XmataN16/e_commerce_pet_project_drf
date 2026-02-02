# accounts/auth_utils.py
import jwt
import uuid
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=30)
JWT_ALGORITHM = "HS256"

def create_access_token(user):
    now = datetime.utcnow()
    jti = str(uuid.uuid4())
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "iat": now,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, jti, payload["exp"]

def create_refresh_token():
    # raw token returned to client; hashed stored in DB
    raw = secrets.token_urlsafe(48)
    expires_at = timezone.now() + REFRESH_TOKEN_LIFETIME
    return raw, expires_at
