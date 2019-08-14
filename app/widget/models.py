from django.db import models
from django.conf import settings

from measurement.models import Metric
from nslc.models import ChannelGroup


class WidgetBase(models.Model):
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


class Widget_Type(WidgetBase):
    type = models.CharField(max_length=255)


class Widget(WidgetBase):
    widget_type = models.ForeignKey(
        Widget_Type,
        on_delete=models.CASCADE,
        related_name='widgets',
    )
    channel_group = models.ForeignKey(
        ChannelGroup,
        on_delete=models.CASCADE,
        related_name='widgets',
    )


class Dashboard(WidgetBase):
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='metric_params'
    )
