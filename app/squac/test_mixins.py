from organization.models import Organization
from django.contrib.auth import get_user_model
import secrets


def sample_user(email='test@pnsn.org', password="secret", organization=None,
                **kwargs):
    '''create a sample user for testing'''
    org = secrets.token_hex(4)
    if not organization:
        organization = Organization.objects.create(name=org)

    return get_user_model().objects.create_user(
        email,
        password,
        organization,
        **kwargs
    )
