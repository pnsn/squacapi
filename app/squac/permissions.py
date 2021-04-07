from rest_framework import permissions
from rest_framework.permissions import DjangoModelPermissions
from organization.models import Organization


''' In summary:
    permission_classes are looped over the defined list.
    has_object_permission method is called after has_permission
    method returns value True except in POST method
    (in POST method has_permission only be executed).
    When False value is returned from the permission_classes method,
    the request gets no permission and will not loop more,
    otherwise, it checks all permissions on looping.
    has_permission method will be called on all
    (GET, POST, PUT, DELETE) HTTP request.
    has_object_permission method will not be called on
    HTTP POST request, hence we need to restrict it from has_permission method.

 https://www.django-rest-framework.org/api-guide/permissions/
 #object-level-permissions

 NOTE: has_object_permission is not called on list AND not called when
    queryset is 404. Since queryset is scoped to user this means that a user
    without object level permissions will 404 NOT 403!

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


class IsOrgAdminOrMember(DjangoModelPermissions):
    ''' Custom to check if user belongs to org'''

    def has_permission(self, request, view):
        '''if user is staff or if SAFE request, we're done
            otherwise check model object perms

            try for user object
                if request.user is member or admin of org check perms
            except:
                this is org object, check permissions
        '''

        if request.user.is_staff or request.method in permissions.SAFE_METHODS:
            return True
        try:
            org = Organization.objects.get(pk=request.data['organization'])
            is_in_org = org.is_admin(request.user) or \
                org.is_member(request.user)
            return is_in_org and super().has_permission(request, view)
        except KeyError:
            return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        ''' Create not called by this method since object doesn't exist
            This is called after queryset, so if queryset is scoped for
            this, it will 404 without this method ever called.
            Perm order:
            if user is admin or org admin all allowable model methods
            if user is member, read methods
        '''
        try:
            '''is this is a user object? No? then AttributeError'''
            obj.organization_id
            org = Organization.objects.get(pk=obj.organization_id)
        except AttributeError:
            '''org object'''
            org = obj
        org_admin = org.is_admin(request.user)
        if request.user.is_staff or org_admin:
            return True
        return request.method in permissions.SAFE_METHODS


class IsAdminOrOwner(DjangoModelPermissions):
    '''extends DjanoModelPermissions and adds object level perms'''

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or obj.user == request.user:
            return True
        return False
