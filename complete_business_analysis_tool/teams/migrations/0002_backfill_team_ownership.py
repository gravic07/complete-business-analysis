"""Step 2 of 3: put all pre-Teams data and Users into one Team.

Runs between the migrations that add Client.team and the four created_by
fields as nullable (step 1) and those that make them NOT NULL (step 3).
"""

from django.db import migrations

DEFAULT_TEAM_NAME = "Peak Performance Partners"

CREATED_BY_MODEL_LABELS = [
    ("clients", "Client"),
    ("assessments", "Assessment"),
    ("reports", "Feedback"),
    ("reports", "PDFExport"),
]


def backfill_team_ownership(apps, schema_editor):
    User = apps.get_model("users", "User")
    Team = apps.get_model("teams", "Team")
    Client = apps.get_model("clients", "Client")

    created_by_models = [apps.get_model(*label) for label in CREATED_BY_MODEL_LABELS]
    has_owned_rows = any(model.objects.exists() for model in created_by_models)

    if not has_owned_rows and not User.objects.exists():
        return

    backfill_user = (
        User.objects.filter(is_superuser=True).order_by("date_joined", "pk").first()
        or User.objects.order_by("date_joined", "pk").first()
    )
    if backfill_user is None:
        msg = (
            "Cannot backfill Team ownership: Clients, Assessments, Feedback or "
            "PDF exports exist but there are no Users to record as their creator. "
            "Run `manage.py createsuperuser`, then migrate again."
        )
        raise RuntimeError(msg)

    team = Team.objects.create(name=DEFAULT_TEAM_NAME)
    User.objects.update(team=team)
    Client.objects.update(team=team)
    for model in created_by_models:
        model.objects.update(created_by=backfill_user)


def reverse_backfill_team_ownership(apps, schema_editor):
    User = apps.get_model("users", "User")
    Client = apps.get_model("clients", "Client")

    User.objects.filter(team__name=DEFAULT_TEAM_NAME).update(team=None)
    Client.objects.update(team=None)
    for label in CREATED_BY_MODEL_LABELS:
        apps.get_model(*label).objects.update(created_by=None)


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0001_initial"),
        ("users", "0002_user_team"),
        ("clients", "0005_client_team_client_created_by"),
        ("assessments", "0007_assessment_created_by"),
        ("reports", "0012_feedback_created_by_pdfexport_created_by"),
    ]

    operations = [
        migrations.RunPython(
            backfill_team_ownership,
            reverse_backfill_team_ownership,
        ),
    ]
