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
