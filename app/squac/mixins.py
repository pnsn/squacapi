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
            otherwise check model permissions.

            objecect level permissions can then be appended by setting
            object_permissions on the view
    '''
    # base permission classes
    permission_classes = (
        IsAuthenticated, IsAdminUser | DjangoModelPermissions)
    # object level permissions are set in view
    object_permissions = ()

    # append object perms to base
    def get_permissions(self):
        self.permission_classes += self.object_permissions
        return super(PermissionsMixin, self).get_permissions()
