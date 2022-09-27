from rest_framework.permissions import IsAuthenticated, \
    DjangoModelPermissions, IsAdminUser
from squac.permissions import IsAdminOwnerOrShared, IsOrgAdminOrMember,\
    IsAdminOrOwner

'''common mixins'''


class SetUserMixin:
    '''Set user on create'''
    # all models that require user

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AdminOrOwnerPermissionMixin:
    '''Admin or Owner Permissions
        permission_classes acts as base permissions:
            all views must be autheticated and if user is admin we are done
            otherwise check if user owns object
            ',' commas act as 'and' '|' pipes act as 'or'
         '''
    permission_classes = (
        IsAuthenticated, IsAdminOrOwner,)


class DefaultPermissionsMixin:
    '''Default Permissions

        permission_classes acts as base permissions:
            all views must be autheticated and if user is admin we are done
            otherwise check model permission.
            ',' commas act as 'and' '|' pipes act as 'or'
         '''
    permission_classes = (
        IsAuthenticated, (IsAdminUser | DjangoModelPermissions),)


class SharedPermissionsMixin:
    '''Shared Permissions

            all views must be autheticated and if user is admin we are done
            otherwise check shared fields share_all, share_org
            for read actions
            ',' commas act as 'and' '|' pipes act as 'or'
         '''
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrShared,)


class OrganizationPermissionsMixin:
    '''Organization Permissions

            Organizations admins need to add/edit/delete users and to make
            other users organization admins
            ',' commas act as 'and' '|' pipes act as 'or'
         '''
    permission_classes = (
        IsAuthenticated, IsOrgAdminOrMember,)
