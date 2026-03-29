from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send a test email using the currently configured email backend."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Recipient email address.")

    def handle(self, *args, **options):
        recipient = options["to"]
        if not settings.DEFAULT_FROM_EMAIL:
            raise CommandError("DEFAULT_FROM_EMAIL is not configured.")

        send_mail(
            subject="Reflexia email test",
            message=(
                "This is a test email from Reflexia.\n\n"
                "If you received it, the email backend is configured correctly."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}."))
