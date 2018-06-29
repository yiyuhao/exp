# coding=utf-8
from rest_framework import permissions
from django.contrib.auth.models import Group


class IsStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_permission(self, request, view):
        user = request.user
        return user.is_staff and user.is_active

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser and user.is_active

def staffCheck(user):
    return user.is_staff and user.is_active


def is_warehouse_manager(user):
    isManger = user.groups.filter(name='仓库主管').exists()
    return user.is_superuser or (user.is_staff and user.is_active and isManger)

def is_package_manager(user):
    isPackagerManager = user.groups.filter(name='仓库打板').exists()
    return is_warehouse_manager(user) or (user.is_staff and user.is_active and isPackagerManager)

