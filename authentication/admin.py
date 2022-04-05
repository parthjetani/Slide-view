from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


# Register your models here.
class CustomUserinline(admin.StackedInline):
    model = CustomUser
    can_delete = False
    verbose_name_plural = 'Organization'


class CustomizedUserAdmin (UserAdmin):
    inlines = (CustomUserinline, )


admin.site.unregister(User)
admin.site.register(User, CustomizedUserAdmin)
