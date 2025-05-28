from django.contrib import admin
from .models import RefreshToken, LoginAttempt, Permission, Role, UserRole


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'is_blacklisted']
    list_filter = ['is_blacklisted', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'attempt_type', 'ip_address', 'timestamp']
    list_filter = ['attempt_type', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['timestamp']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource_type', 'action_type', 'is_active']
    list_filter = ['resource_type', 'action_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_system_role', 'is_active', 'created_at']
    list_filter = ['is_system_role', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active', 'assigned_at', 'expires_at']
    list_filter = ['role', 'is_active', 'assigned_at']
    search_fields = ['user__username', 'role__name']
