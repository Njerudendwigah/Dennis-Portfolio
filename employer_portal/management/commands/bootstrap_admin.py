import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the temporary production staff account."

    def handle(self, *args, **options):
        username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME")
        email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

        if not username or not email or not password:
            raise CommandError("Bootstrap admin environment variables are incomplete.")

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"Bootstrap admin account {action} successfully."
        ))
