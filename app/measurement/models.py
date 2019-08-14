from django.db import models
from django.conf import settings

from nslc.models import Channel


class MeasurementBase(models.Model):
    '''Base class for all measurement models'''
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


class DataSource(MeasurementBase):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')


class Metric(MeasurementBase):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    unit = models.CharField(max_length=255)
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='metrics',
    )


class Measurement(MeasurementBase):
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    value = models.FloatField()
    starttime = models.DateTimeField()
    endtime = models.DateTimeField()

    def __str__(self):
        return "Metric: {str(self.metric)} Channel: {str(self.channel)}"
