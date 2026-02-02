from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.conf import settings
from .serializers import RegisterSerializer, LoginSerializer
from .auth_utils import create_access_token, create_refresh_token
from .models import RefreshToken, JWTBlacklist
from django.contrib.auth import authenticate

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        # optionally assign default role
        return Response({"id": user.id, "email": user.email}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"]
        password = ser.validated_data["password"]
        # authenticate - we use email as username field
        user = authenticate(request, username=email, password=password)
        if user is None or not user.is_active:
            return Response({"detail": "Invalid credentials or inactive"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token, jti, access_exp = create_access_token(user)
        raw_refresh, refresh_exp = create_refresh_token()
        # store hashed refresh
        hashed = RefreshToken.hash_token(raw_refresh)
        rt = RefreshToken.objects.create(user=user, token_hash=hashed, expires_at=refresh_exp,
                                         ip=request.META.get("REMOTE_ADDR"), user_agent=request.META.get("HTTP_USER_AGENT"))
        return Response({
            "access_token": access_token,
            "access_expires": access_exp,
            "refresh_token": raw_refresh,
            "refresh_expires": refresh_exp,
        }, status=status.HTTP_200_OK)

class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # expects { "refresh_token": "<raw>" }
        raw = request.data.get("refresh_token")
        if not raw:
            return Response({"detail":"refresh_token required"}, status=400)
        hashed = RefreshToken.hash_token(raw)
        try:
            rt = RefreshToken.objects.get(token_hash=hashed)
        except RefreshToken.DoesNotExist:
            return Response({"detail":"Invalid refresh token"}, status=401)
        if rt.revoked or rt.is_expired():
            return Response({"detail":"Refresh token revoked or expired"}, status=401)
        user = rt.user
        access_token, jti, access_exp = create_access_token(user)

        # rotate refresh (optional): create new, revoke old
        raw_new, new_exp = create_refresh_token()
        rt.revoked = True
        rt.save()
        RefreshToken.objects.create(user=user, token_hash=RefreshToken.hash_token(raw_new), expires_at=new_exp)
        return Response({
            "access_token": access_token,
            "access_expires": access_exp,
            "refresh_token": raw_new,
            "refresh_expires": new_exp,
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # expects refresh_token in body to revoke; also blacklist jti if provided
        raw = request.data.get("refresh_token")
        jti = None
        # revoke refresh if provided
        if raw:
            hashed = RefreshToken.hash_token(raw)
            RefreshToken.objects.filter(token_hash=hashed, user=request.user).update(revoked=True)
        # blacklist current access token jti (if present)
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split()[1]
            import jwt
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
                jti = payload.get("jti")
            except Exception:
                jti = None
        if jti:
            JWTBlacklist.objects.create(jti=jti, expires_at=timezone.now())  # expires_at optional
        return Response({"detail":"logged out"}, status=200)
    
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()
        # revoke all refresh tokens & blacklist current access token
        RefreshToken.objects.filter(user=user).update(revoked=True)
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split()[1]
            import jwt
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
                jti = payload.get("jti")
                if jti:
                    JWTBlacklist.objects.create(jti=jti)
            except Exception:
                pass
        return Response({"detail":"account soft-deleted"}, status=200)
