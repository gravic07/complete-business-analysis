from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "business_name",
        "first_name",
        "last_name",
        "title",
        "industry",
        "created_at",
    ]
    list_filter = ["industry"]
    search_fields = ["business_name", "first_name", "last_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["business_name"]
