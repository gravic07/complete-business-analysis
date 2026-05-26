from django.contrib import admin

from .models import CategoryFeedback, CategorySection, ExecutiveSummary, Feedback


class CategorySectionInline(admin.TabularInline):
    model = CategorySection
    fields = ("category", "overview", "impact", "path_forward", "created_at")
    readonly_fields = ("category", "overview", "impact", "path_forward", "created_at")
    extra = 0
    can_delete = False


class ExecutiveSummaryInline(admin.TabularInline):
    model = ExecutiveSummary
    fields = ("content", "created_at")
    readonly_fields = ("content", "created_at")
    extra = 0
    can_delete = False


@admin.register(CategorySection)
class CategorySectionAdmin(admin.ModelAdmin):
    list_display = ("analysis", "category", "created_at")
    list_filter = ("category",)
    readonly_fields = (
        "analysis",
        "category",
        "overview",
        "impact",
        "path_forward",
        "created_at",
        "updated_at",
    )
    search_fields = ("analysis__assessment__client__business_name", "overview")

    def has_add_permission(self, request):
        return False


@admin.register(ExecutiveSummary)
class ExecutiveSummaryAdmin(admin.ModelAdmin):
    list_display = ("analysis", "created_at")
    readonly_fields = ("analysis", "content", "created_at", "updated_at")
    search_fields = ("analysis__assessment__client__business_name", "content")

    def has_add_permission(self, request):
        return False


class CategoryFeedbackInline(admin.TabularInline):
    model = CategoryFeedback
    fields = ("category", "text")
    readonly_fields = ("category", "text")
    extra = 0
    can_delete = False


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("assessment", "report_feedback", "created_at")
    readonly_fields = ("assessment", "report_feedback", "created_at", "updated_at")
    inlines = [CategoryFeedbackInline]
