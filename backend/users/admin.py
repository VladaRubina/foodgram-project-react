from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """UserAdmin class."""

    model = User
    ordering = ('email',)
    search_fields = ('username', 'email',)
    empty_value_display = '-filter-'
