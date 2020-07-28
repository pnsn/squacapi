from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core import models


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    # list
    list_display = ['email', 'firstname', 'lastname']
    # edit user form
    fieldsets = (
        (None, {'fields': ('email', )}),
        ('Personal Info', {'fields': (
            'firstname',
            'lastname',
        )}),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        ('Groups', {'fields': ('groups', )}),
        ('Important dates', {'fields': ('last_login',)}),)

    # Add new user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),)


admin.site.register(models.User, UserAdmin)
