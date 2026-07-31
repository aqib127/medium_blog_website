from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSettings, Follow

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'handle', 'is_active', 'date_joined')
    search_fields = ('email', 'name', 'handle')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'handle', 'bio', 'location', 'twitter', 'github', 'website', 'avatar', 'avatar_color')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'handle', 'password1', 'password2'),
        }),
    )
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserSettings)
admin.site.register(Follow)