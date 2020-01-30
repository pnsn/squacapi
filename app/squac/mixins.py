from rest_framework.permissions import IsAuthenticated, \
    DjangoModelPermissions, IsAdminUser
'''common mixins'''


class SetUserMixin:
    '''Set user on create'''
    # all models that require user
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PermissionsMixin:
    '''Permissions

        permission_classes acts as base permissions:
            all views must be autheticated and if user is admin we are done
            otherwise check model permission.
         '''
    permission_classes = (
        IsAuthenticated, (IsAdminUser | DjangoModelPermissions),)
    # object_permissions = ()

    '''this didn't pan out but leaving it in for now

        the idea was to set object level permissions on views, and append
        to the permission classes above. The problme being that they appended
        permissions act as an '&' while they were needed as part of the 'or'
        with DjangoModelPermissions e.g.:

        IsAuthenticated, (IsAdminUser |
             DjangoModelPermissions & cond1 & cond2),)

    '''
    # def get_permissions(self):
    #     self.permission_classes += self.object_permissions
    #     return super(PermissionsMixin, self).get_permissions()
