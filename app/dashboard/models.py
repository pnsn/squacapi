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
    share_all = models.BooleanField(default=False)
    share_org = models.BooleanField(default=False)
    window_seconds = models.IntegerField(blank=True, null=True)
    starttime = models.DateTimeField(blank=True, null=True)
    endtime = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )

    class Meta:
        indexes = [
            models.Index(fields=['share_all']),
            models.Index(fields=['share_org'])
        ]


class Widget(DashboardBase):
    '''describes the widget'''
    metrics = models.ManyToManyField('measurement.Metric')

    class Colors(models.TextChoices):
        SQUAC = 'squac'

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
        related_name='widgets',
    )
    channel_group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    columns = models.IntegerField()
    rows = models.IntegerField()
    x_position = models.IntegerField()
    y_position = models.IntegerField()
    color_pallet = models.CharField(
        max_length=24,
        choices=Colors.choices,
        default=Colors.SQUAC
    )
