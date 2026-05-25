from django.contrib import admin

from .models import CategoryFeedback, Feedback, ReportSection


class ReportSectionInline(admin.TabularInline):
    model = ReportSection
    fields = ("category", "content", "created_at")
    readonly_fields = ("category", "content", "created_at")
    extra = 0
    can_delete = False


@admin.register(ReportSection)
class ReportSectionAdmin(admin.ModelAdmin):
    list_display = ("analysis", "category", "created_at")
    list_filter = ("category",)
    readonly_fields = ("analysis", "category", "content", "created_at", "updated_at")
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
    list_display = ("assessment", "overall_text", "created_at")
    readonly_fields = ("assessment", "overall_text", "created_at", "updated_at")
    inlines = [CategoryFeedbackInline]
