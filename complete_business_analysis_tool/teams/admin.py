from django.contrib import admin

from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["name"]
