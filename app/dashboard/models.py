from django.db import models
from django.conf import settings

from nslc.models import Group


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

    def __str__(self):
        return self.name

    def class_name(self):
        return self.__class__.__name__.lower()


class WidgetType(DashboardBase):
    type = models.CharField(max_length=255)


class Dashboard(DashboardBase):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )


class Widget(DashboardBase):
    metrics = models.ManyToManyField('measurement.Metric')
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    widgettype = models.ForeignKey(
        WidgetType,
        on_delete=models.CASCADE,
        related_name='widgets',
    )
