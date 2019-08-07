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
        return f"Metric: {str(self.metric)} Channel: {str(self.channel)}"


class Group(MeasurementBase):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    is_public = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='measurementgroups'
    )


class MetricGroup(MeasurementBase):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='metricgroups'
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='metricgroups'
    )

    def __str__(self):
        return f"Group: {str(self.group)} Metric: {str(self.metric)}"


class Threshold(MeasurementBase):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    min = models.FloatField()
    max = models.FloatField()
    metricgroup = models.ForeignKey(
        MetricGroup,
        on_delete=models.CASCADE,
        related_name='thresholds',
    )


class Alarm(MeasurementBase):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    period = models.IntegerField()
    num_period = models.IntegerField()
    threshold = models.ForeignKey(
        Threshold,
        on_delete=models.CASCADE,
        related_name='alarms',
    )


class Trigger(MeasurementBase):
    count = models.IntegerField()
    alarm = models.ForeignKey(
        Alarm,
        on_delete=models.CASCADE,
        related_name='triggers'
    )

    def __str__(self):
        return f'Alarm: {str(self.alarm)} Count: {str(self.count)}'
