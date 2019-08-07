from django.db import models
from django.conf import settings

from nslc.models import Channel


class DataSource(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Metric(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    unit = models.CharField(max_length=255)
    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='metrics',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Measurement(models.Model):
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
    )
    value = models.FloatField()
    starttime = models.DateTimeField()
    endtime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )


class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='measurementgroups'
    )

    def __str__(self):
        return self.name


class MetricGroup(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Threshold(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    min = models.FloatField()
    max = models.FloatField()
    metricgroup = models.ForeignKey(
        MetricGroup,
        on_delete=models.CASCADE,
        related_name='thresholds',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Alarm(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    period = models.IntegerField()
    num_period = models.IntegerField()
    threshold = models.ForeignKey(
        Threshold,
        on_delete=models.CASCADE,
        related_name='alarms',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Trigger(models.Model):
    count = models.IntegerField()
    alarm = models.ForeignKey(
        Alarm,
        on_delete=models.CASCADE,
        related_name='triggers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{str(self.alarm)}: {str(self.count)}'
