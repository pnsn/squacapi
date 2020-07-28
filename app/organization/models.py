from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_member(self, user):
        return self == user.organization

    def is_admin(self, user):
        return self == user.organization and user.is_org_admin

    def is_owner(self, user):
        return self.owner == user

    def __str__(self):
        return self.name

    def class_name(self):
        return self.__class__.__name__.lower()
