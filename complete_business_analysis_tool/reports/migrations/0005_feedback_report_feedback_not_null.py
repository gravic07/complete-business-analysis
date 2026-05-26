from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0004_structured_models"),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE reports_feedback SET report_feedback = '' WHERE report_feedback IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="feedback",
            name="report_feedback",
            field=models.TextField(blank=True),
        ),
    ]
