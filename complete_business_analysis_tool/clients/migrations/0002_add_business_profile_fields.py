from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="company_size",
            field=models.CharField(
                choices=[
                    ("1_4", "1–4"),
                    ("5_19", "5–19"),
                    ("20_49", "20–49"),
                    ("50_100", "50–100"),
                    ("101_plus", "101+"),
                ],
                default="1_4",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="client",
            name="revenue",
            field=models.CharField(
                choices=[
                    ("under_1m", "$1 million or less"),
                    ("1m_2_5m", "$1 million – $2.5 million"),
                    ("2_5m_10m", "$2.5 million – $10 million"),
                    ("10m_50m", "$10 million – $50 million"),
                    ("over_50m", "$50+ million"),
                ],
                default="under_1m",
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="client",
            name="corporate_style",
            field=models.CharField(
                choices=[
                    ("family_owned", "Family-Owned"),
                    ("sole_proprietorship", "Sole Proprietorship"),
                    ("board_governed", "Board-governed / Corporate"),
                    ("partnership", "Partnership"),
                ],
                default="sole_proprietorship",
                max_length=25,
            ),
            preserve_default=False,
        ),
    ]
