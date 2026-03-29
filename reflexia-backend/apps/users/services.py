from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from apps.users.models import Therapist


@transaction.atomic
def register_therapist(*, first_name, last_name, email, password, license_number, specialty):
    validate_password(password)

    therapist = Therapist.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        license_number=license_number,
        specialty=specialty,
    )
    return therapist
