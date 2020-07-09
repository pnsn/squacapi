from rest_framework import permissions
from rest_framework.permissions import DjangoModelPermissions
from organizations.models import Organization


class IsAdminOwnerOrShared(DjangoModelPermissions):
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
            * if has_perm and safe method check for share_all, share_org
            * update, partial_update and destroy check for owner
            * create not called by this method since object doesn't exist
        '''
        if request.user.is_staff:
            return True
        has_permission = super().has_permission(request, view)
        if has_permission and request.method in permissions.SAFE_METHODS:
            if obj.user == request.user:
                return True
            try:
                org_id = obj.organization_id
                org = Organization.objects.get(pk=org_id)
                if obj.share_all or \
                        obj.share_org and org.is_member(request.user):
                    return True
            except AttributeError:
                return False
