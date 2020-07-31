from organization.models import Organization
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as UserGroup, Permission

import secrets


def sample_user(email='test@pnsn.org', password="secret", organization=None,
                **kwargs):
    '''create a sample user for testing'''
    org = secrets.token_hex(4)
    # for testing override is_active default
    if 'is_active' not in kwargs:
        kwargs['is_active'] = True
    if not organization:
        organization = Organization.objects.create(name=org)

    return get_user_model().objects.create_user(
        email,
        password,
        organization,
        **kwargs
    )


''' permissons follow form

    view_model
    add_model
    change_model
    delete_model

    Widget types and stattypes use modelpermissions only so no need to test
    beyond has_perm
'''


def create_group(name, permissions):
    '''takes name of group and list of permissions'''
    group = UserGroup.objects.create(name=name)
    for p in permissions:
        perm = Permission.objects.get(codename=p)
        group.permissions.add(perm)
    return group
