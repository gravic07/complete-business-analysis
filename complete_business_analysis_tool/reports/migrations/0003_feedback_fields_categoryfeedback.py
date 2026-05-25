import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0002_assessment_client"),
        ("reports", "0002_reportsection"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedback",
            name="assessment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="feedbacks",
                to="assessments.assessment",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="feedback",
            name="overall_text",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="CategoryFeedback",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("text", models.TextField()),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="category_feedbacks",
                        to="assessments.category",
                    ),
                ),
                (
                    "feedback",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_feedbacks",
                        to="reports.feedback",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
    ]
