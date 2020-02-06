from rest_framework import permissions
from rest_framework.permissions import DjangoModelPermissions


class IsAdminOwnerOrPublicReadOnly(DjangoModelPermissions):
    '''extends DjanoModelPermissions and adds object level perms'''

    def has_permission(self, request, view):
        '''has permission

            needed since create doesn't call get_object, which in turn doesn't
            call has_object_permission
        '''

        if request.user.is_staff:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        '''Perm order:

            * if user is_staff they are god
            * check perms
            * if has_perm and safe method check for is_public
            * update, partial_update and destroy check for owner
            * create not called by this method since object doesn't exist
        '''
        if request.user.is_staff:
            return True
        has_permission = super().has_permission(request, view)
        if has_permission and request.method in permissions.SAFE_METHODS:
            try:
                return obj.is_public
            except AttributeError:
                # if user has perm and obj doesn't have an is_public
                return True

        if has_permission and view.action in ['update', 'partial_update',
                                              'destroy']:
            return obj.user == request.user
        return False


# For testing
class IsTrue(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        print("wow true")
        return True


class IsFalse(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        print("big ol false")
        return False
