import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    def validate(self, password, user=None):
        errors = []

        if len(password) < 8:
            errors.append("La contrasenya ha de tenir almenys 8 caràcters.")
        if not re.search(r"[A-Z]", password):
            errors.append("La contrasenya ha de tenir almenys una lletra majúscula.")
        if not re.search(r"[a-z]", password):
            errors.append("La contrasenya ha de tenir almenys una lletra minúscula.")
        if not re.search(r"\d", password):
            errors.append("La contrasenya ha de tenir almenys un número.")
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("La contrasenya ha de tenir almenys un caràcter especial.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "La contrasenya ha de contenir almenys 8 caràcters, una lletra majúscula, "
            "una lletra minúscula, un número i un caràcter especial."
        )
