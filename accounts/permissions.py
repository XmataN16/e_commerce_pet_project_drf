# accounts/permissions.py
from .models import Permission, RolePermission, UserRole

def get_user_roles(user):
    return [ur.role for ur in user.user_roles.select_related("role").all()]

def user_has_perm(user, perm_code):
    # superusers get everything
    if user.is_superuser:
        return True
    # gather user roles
    roles = get_user_roles(user)
    if not roles:
        return False
    # check RolePermission join
    return RolePermission.objects.filter(role__in=roles, perm__code=perm_code).exists()
