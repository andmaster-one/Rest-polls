from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def get_custom_permission(self, *args, **kwargs):
        request = kwargs.pop('request')
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return self.get_custom_permission(request=request)

    def has_permission(self, request, view):
        return self.get_custom_permission(request=request)
