from rest_framework import permissions


class IsReadOnly(permissions.BasePermission):
    """IsReadOnly

        Allow read resource
     """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS


class IsPublicReadOnly(permissions.BasePermission):
    '''Is PublicReadOnly

        Allow read on resource marked is_public
    '''
    def has_object_permission(self, request, view, obj):
        try:
            obj.is_public
        except AttributeError:
            return False
        return request.method in permissions.SAFE_METHODS and obj.is_public


class IsOwner(permissions.BasePermission):
    """IsOwner

        Allow owner to perform reads and writes on their own resource
     """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
