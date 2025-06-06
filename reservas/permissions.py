from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsReservationOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='owners').exists()
