from django.db import migrations, models
import django.conf


class Migration(migrations.Migration):
    dependencies = [
        ("employer_portal", "0006_alter_document_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="PortfolioContent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=80, unique=True)),
                ("data", models.JSONField(default=dict)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="portfolio_content_updates",
                        to=django.conf.settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["key"],
            },
        ),
    ]
