from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _


def validate_email_list(email_list):
    if not email_list:
        # Empty list or None is fine (assuming level is 1)
        return email_list

    # First check if it an actual list and not some other json object
    if not isinstance(email_list, list) and not isinstance(email_list, str):
        raise ValidationError(
            _(f"Invalid input type. Requires str or list,"
              f" this is of type {type(email_list)}")
        )

    # Just make a string a list so below logic works
    if isinstance(email_list, str):
        email_list = [email_list]

    invalid = []
    for email in email_list:
        try:
            validate_email(email)
        except ValidationError:
            invalid.append(email)

    if invalid:
        raise ValidationError(
            _(f"Invalid email address(es): [{', '.join(invalid)}]")
        )
    else:
        return email_list
