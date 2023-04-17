from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_email


class EmailListArrayField(ArrayField):
    """
    A field that allows us to store an array of emails.

    Uses Django 1.9's postgres ArrayField
    and a EmailField for its formfield.

    Usage:

        emails = EmailListArrayField(models.EmailField(max_length=...,
                                                    choices=(...,)),
                                   default=[...])
    """

    def to_python(self, value):
        ''' Take value and ensure it is correct type for internals'''
        if not value:
            return None

        ''' lists stay as lists'''
        if isinstance(value, list):
            return value

        ''' split string by separators and turn into list'''
        if isinstance(value, str):
            return [address.strip() for address in value.split(',')]
        else:
            raise ValidationError(
                _(f"Invalid input type. Requires str or list,"
                  f" this is of type {type(value)}"))

    def validate(self, value, *args):
        super().validate(value, *args)
        for email in value:
            validate_email(email)
