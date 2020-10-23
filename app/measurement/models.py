from django.db import models
from django.conf import settings
from dashboard.models import Widget
from nslc.models import Channel, Group
from django.db.models import Avg, Max, Min, Sum

from datetime import date, datetime, timedelta
import pytz


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


class Metric(MeasurementBase):
    '''Describes the kind of metric'''

    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    unit = models.CharField(max_length=255)
    url = models.CharField(max_length=255, default='', blank=True)
    default_minval = models.FloatField(blank=True, null=True)
    default_maxval = models.FloatField(blank=True, null=True)
    reference_url = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]


class Measurement(MeasurementBase):
    '''describes the observable metrics'''
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

    class Meta:
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-starttime']),
            models.Index(fields=['-endtime']),
            models.Index(fields=['value'])

        ]

    def __str__(self):
        return f"Metric: {str(self.metric)} Channel: {str(self.channel)}"


class Threshold(MeasurementBase):
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='thresholds')

    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='thresholds')
    minval = models.FloatField(blank=True, null=True)
    maxval = models.FloatField(blank=True, null=True)
    band_inclusive = models.BooleanField(default=True)

    def __str__(self):
        return (f"Threshold for Widget: {str(self.widget)} "
                f"Metric: {str(self.metric)}"
                f"Min {self.minval}"
                f"Max {self.maxval}"
                )


class Alarm(MeasurementBase):
    '''Describes alarms on metrics and channel_groups'''

    # Define choices for interval_type. Use TextChoices if in Django >3.0
    MINUTE = 'minute'
    HOUR = 'hour'
    DAY = 'day'

    INTERVAL_TYPE_CHOICES = [
        (MINUTE, "Minute"),
        (HOUR, "Hour"),
        (DAY, "Day")
    ]

    # Define choices for stat. Use TextChoices if in Django >3.0
    SUM = 'sum'
    MEAN = 'mean'
    MEDIAN = 'median'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'

    STAT_CHOICES = [
        (SUM, "Sum"),
        (MEAN, "Mean"),
        (MEDIAN, "Median"),
        (MINIMUM, "Minimum"),
        (MAXIMUM, "Maximum")
    ]

    channel_group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='alarms'
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='alarms'
    )
    interval_type = models.CharField(max_length=8,
                                     choices=INTERVAL_TYPE_CHOICES,
                                     default=HOUR
                                     )
    interval_count = models.IntegerField()
    num_channels = models.IntegerField()
    stat = models.CharField(max_length=8,
                            choices=STAT_CHOICES,
                            default=SUM
                            )

    def agg_measurements(self, T1=None, T2=None):
        if not T1 or not T2:
            if self.interval_type == self.MINUTE:
                seconds = 60
            elif self.interval_type == self.HOUR:
                seconds = 60 * 60
            elif self.interval_type == self.DAY:
                seconds = 60 * 60 * 24
            else:
                print('Invalid interval type!')
                return
            T2 = datetime.now(tz=pytz.UTC)
            T1 = T2 - timedelta(seconds=seconds)

        group = self.channel_group
        metric = self.metric

        # Get a QuerySet containing only measurements for the correct time
        # period and metric for this alarm
        q = metric.measurements.filter(starttime__range=(T1, T2),
                                       channel__in=group.channels.all()) 
        # Now calculate the aggregate values for each channel
        q = q.values('channel').annotate(Sum('value'),
                                         Avg('value'),
                                         Max('value'),
                                         Min('value'))

        return q

    def __str__(self):
        return (f"{str(self.channel_group)}, "
                f"{str(self.metric)}, "
                f"{self.interval_count} {self.interval_type}, "
                f"{self.num_channels} chan, "
                f"{self.stat}"
                )


class AlarmThreshold(MeasurementBase):
    '''Describe an individual alarm_threshold for an alarm'''
    alarm = models.ForeignKey(
        Alarm,
        on_delete=models.CASCADE,
        related_name='alarm_thresholds'
    )
    # notification = models.ForeignKey(
    #     Notification,
    #     on_delete=models.CASCADE,
    #     related_name='alarm_thresholds'
    # )
    minval = models.FloatField(blank=True, null=True)
    maxval = models.FloatField(blank=True, null=True)
    band_inclusive = models.BooleanField(default=True)
    level = models.IntegerField(default=1)

    def __str__(self):
        return (f"Alarm: {str(self.alarm)}, "
                f"Min: {self.minval}, "
                f"Max: {self.maxval}, "
                f"Level: {self.level}"
                )


class Alert(MeasurementBase):
    '''Describe an alert for an alarm_threshold'''
    alarm_threshold = models.ForeignKey(
        AlarmThreshold,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    timestamp = models.DateTimeField()
    message = models.CharField(max_length=255)
    in_alarm = models.BooleanField(default=True)

    class Meta:
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return (f"Time: {self.timestamp}, "
                f"Alarm: {str(self.alarm_threshold)}"
                )


class Archive(models.Model):
    """An archive-summary of measurements"""

    # TODO: collapse into TextChoices innerclass after Django 3 upgrade
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'

    ARCHIVE_TYPE_CHOICES = [
        (DAY, "Day"),
        (WEEK, "Week"),
        (MONTH, "Month"),
        (YEAR, "Year")
    ]

    archive_type = models.CharField(max_length=8, choices=ARCHIVE_TYPE_CHOICES)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    min = models.FloatField()
    max = models.FloatField()
    mean = models.FloatField()
    median = models.FloatField()
    stdev = models.FloatField()
    num_samps = models.IntegerField()
    starttime = models.DateTimeField(auto_now=False)
    endtime = models.DateTimeField(auto_now=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"Archive of Metric: {str(self.metric)} "
                f"Channel: {str(self.channel)} "
                f"from {format(self.starttime, '%m-%d-%Y')} "
                f"to {format(self.endtime, '%m-%d-%Y')}")
