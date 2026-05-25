from django.contrib import admin

from .models import Analysis, CategoryScore


class CategoryScoreInline(admin.TabularInline):
    model = CategoryScore
    fields = ("category", "score", "max_possible_score")
    readonly_fields = ("category", "score", "max_possible_score")
    extra = 0
    can_delete = False


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("assessment", "status", "total_score", "created_at")
    list_filter = ("status",)
    readonly_fields = (
        "assessment",
        "feedback",
        "status",
        "total_score",
        "created_at",
        "updated_at",
    )
    inlines = [CategoryScoreInline]

    def has_add_permission(self, request):
        return False


@admin.register(CategoryScore)
class CategoryScoreAdmin(admin.ModelAdmin):
    list_display = ("analysis", "category", "score", "max_possible_score")
    readonly_fields = (
        "analysis",
        "category",
        "score",
        "max_possible_score",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
