from django.contrib import admin

from .models import (
    Answer,
    Assessment,
    AssessmentTemplate,
    Category,
    Question,
    QuestionOption,
    TemplateQuestion,
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    fields = ["text", "rank", "weight"]
    extra = 0
    ordering = ["rank"]


class TemplateQuestionInline(admin.TabularInline):
    model = TemplateQuestion
    raw_id_fields = ["question"]
    fields = ["question", "order"]
    extra = 0


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ["question", "selected_option", "question_snapshot", "option_snapshot"]
    readonly_fields = [
        "question",
        "selected_option",
        "question_snapshot",
        "option_snapshot",
    ]
    can_delete = False
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "question_count", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    @admin.display(description="Questions")
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]
    list_display = ["short_body", "category", "option_count", "created_at"]
    list_filter = ["category"]
    search_fields = ["body"]
    readonly_fields = ["id", "created_at", "updated_at"]

    @admin.display(description="Question")
    def short_body(self, obj):
        return obj.body[:80]

    @admin.display(description="Options")
    def option_count(self, obj):
        return obj.options.count()


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateQuestionInline]
    list_display = ["title", "question_count", "assessment_count", "created_at"]
    search_fields = ["title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    @admin.display(description="Questions")
    def question_count(self, obj):
        return obj.template_questions.count()

    @admin.display(description="Assessments")
    def assessment_count(self, obj):
        return obj.assessments.count()


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ["__str__", "client", "template", "answer_count", "created_at"]
    list_filter = ["template", "client__industry"]
    search_fields = ["client__business_name", "template__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    raw_id_fields = ["client", "template"]

    @admin.display(description="Answers")
    def answer_count(self, obj):
        return obj.answers.count()
