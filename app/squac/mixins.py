from rest_framework.permissions import IsAuthenticated, \
    DjangoModelPermissions, IsAdminUser
from squac.permissions import IsAdminOwnerOrShared, IsOrgAdminOrMember,\
    IsAdminOrOwner, IsAdminOwnerOrReadOnly

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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


class OwnerOrReadOnlyPermissionMixin:
    '''Owner or Admin can edit, otherwise read only access

        permission_classes acts as base permissions:
            all views must be autheticated and if user is admin we are done
            otherwise check if user owns object
            ',' commas act as 'and' '|' pipes act as 'or'
         '''
    permission_classes = (
        IsAuthenticated | IsAdminOwnerOrReadOnly,)


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


class EnablePartialUpdateMixin:
    """Enable partial updates

    Override partial kwargs in UpdateModelMixin class
    https://github.com/encode/django-rest-framework/blob/91916a4db14cd6a06aca13fb9a46fc667f6c0682/rest_framework/mixins.py#L64
    """

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


id_params = [
    openapi.Parameter(
        'id',
        openapi.IN_PATH,
        type=openapi.TYPE_INTEGER),
]


class OverrideReadParamsMixin:
    @swagger_auto_schema(manual_parameters=id_params)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class OverrideParamsMixin(OverrideReadParamsMixin):
    """
        Overrides id param documentation for detail operations

    """

    @swagger_auto_schema(manual_parameters=id_params)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=id_params)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=id_params)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
