from django.db import models
from django.conf import settings

from nslc.models import Group
from organization.models import Organization


class DashboardBase(models.Model):
    '''Base class for all widget models'''
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name

    def class_name(self):
        return self.__class__.__name__.lower()


class Dashboard(DashboardBase):

    '''describes the container the holds widgets'''
    properties = models.JSONField(blank=True, null=True)
    share_all = models.BooleanField(default=False)
    share_org = models.BooleanField(default=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )
    channel_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='widgets',
        null=True,
    )

    def save(self, *args, **kwargs):
        return super(Dashboard, self).save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['share_all']),
            models.Index(fields=['share_org'])
        ]


class Widget(DashboardBase):
    '''describes the widget'''
    metrics = models.ManyToManyField('measurement.Metric')

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    properties = models.JSONField(null=True)
    layout = models.JSONField(null=True)
    thresholds = models.JSONField(null=True)
    type = models.CharField(max_length=255, null=True)
    stat = models.CharField(max_length=255, null=True)
