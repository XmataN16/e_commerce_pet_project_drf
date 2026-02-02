# accounts/auth.py
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from rest_framework import authentication, exceptions
from django.conf import settings
from .models import JWTBlacklist, User
from django.utils import timezone

class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header:
            return None
        if auth_header[0].decode().lower() != self.keyword.lower():
            return None
        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        token = auth_header[1].decode()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Access token expired")
        except InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        jti = payload.get("jti")
        if jti:
            # check blacklist
            if JWTBlacklist.objects.filter(jti=jti).exists():
                raise exceptions.AuthenticationFailed("Token revoked")

        user_id = payload.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive")

        return (user, None)
