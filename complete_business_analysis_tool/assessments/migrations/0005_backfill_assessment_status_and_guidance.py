from django.db import migrations, models


def backfill_status_and_guidance(apps, schema_editor):
    Assessment = apps.get_model("assessments", "Assessment")
    Assessment.objects.update(
        status="complete",
        guidance_submitted_at=models.F("created_at"),
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "assessments",
            "0004_assessment_guidance_submitted_at_assessment_status_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(backfill_status_and_guidance, noop_reverse),
    ]
