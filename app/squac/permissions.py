from rest_framework import permissions
from rest_framework.permissions import DjangoModelPermissions
from organizations.models import Organization

'''
Model permissions are set in the admin section on groups. A user is then added
to those groups

Object permissions are related to the object,
    * owner, who created the object, can perform all actions
    * shared, relates to dashboards and channel groups and is read only
    *
'''


class IsAdminOwnerOrShared(DjangoModelPermissions):
    '''extends DjanoModelPermissions and adds object level perms'''

    def has_permission(self, request, view):

        '''has permission
            called before has_object_permission
            check for is_staff, then check model permissions
            if all true, then has_object permission called
        '''
        if request.user.is_staff:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        '''Create not called by this method since object doesn't exist
            Perm order:
            if Admin or user owns resource, all actions
            else (for read actions)
                * check group perms  (reporter, viewer, contributer)
                * if has_perm and safe method check for share_all, share_org

        '''

        if request.user.is_staff or obj.user == request.user:
            return True
        has_permission = super().has_permission(request, view)
        if has_permission and request.method in permissions.SAFE_METHODS:
            try:
                org_id = obj.organization_id
                org = Organization.objects.get(pk=org_id)
                if obj.share_all or \
                        obj.share_org and org.is_member(request.user):
                    return True
            except AttributeError:
                return False


class IsAdminOrOrganizationAdmin():
    ''' Custom to check if user belongs to org'''

    def has_permission(self, request, view):
        '''on create object doesn't exist but request objects
            has organizatin id

        '''
        try:
            org = Organization.objects.get(pk=request.data['organization'])
            return request.user.is_staff or org.is_admin(request.user)
        except KeyError:
            return True

    def has_object_permission(self, request, view, obj):
        ''' Create not called by this method since object doesn't exist
            Perm order:
            if user is admin or org admin all methods
            if user is member, read methods 
        '''
        try:
            admin = obj.is_admin(request.user)
            member = obj.is_member(request.user)

            return request.user.is_staff or \
                request.method in permissions.SAFE_METHODS and \
                (admin or member)

        except TypeError:
            # we have an org user
            org = Organization.objects.get(pk=obj.organization_id)
            admin = org.is_admin(request.user)
            member = org.is_member(request.user)
            if request.user.is_staff or admin:
                return True
            return request.method in permissions.SAFE_METHODS and member
