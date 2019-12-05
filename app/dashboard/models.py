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
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name

    def class_name(self):
        return self.__class__.__name__.lower()


class WidgetType(DashboardBase):
    '''describes the type of widget'''
    type = models.CharField(max_length=255, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['type'])
        ]


class StatType(DashboardBase):
    '''describes the stat used on widget'''
    type = models.CharField(max_length=255, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['type'])
        ]


class Dashboard(DashboardBase):
    '''describes the container the holds widgets'''
    pass


class Widget(DashboardBase):
    '''describes the widget'''
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
    stattype = models.ForeignKey(
        StatType,
        on_delete=models.CASCADE,
        related_name='stat',
    )
    channel_group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )
    columns = models.IntegerField()
    rows = models.IntegerField()
    x_position = models.IntegerField()
    y_position = models.IntegerField()
