from django.db import models
from django.db.models import Avg, Count, Max, Min, Sum
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.models import Notification
from dashboard.models import Widget
from nslc.models import Channel, Group

from datetime import datetime, timedelta
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

        ]

    def __str__(self):
        return (f"Metric: {str(self.metric)} "
                f"Channel: {str(self.channel)} "
                f"starttime: {format(self.starttime, '%m-%d-%Y %M:%S')} "
                f"endtime: {format(self.endtime, '%m-%d-%Y %M:%S')} "
                )


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

    # Define choices for interval_type
    class IntervalType(models.TextChoices):
        MINUTE = 'minute', _('Minute')
        HOUR = 'hour', _('Hour')
        DAY = 'day', _('Day')

    # Define choices for stat
    # These need to match the field names used in agg_measurements
    class Stat(models.TextChoices):
        COUNT = 'count', _('Count')
        SUM = 'sum', _('Sum')
        AVERAGE = 'avg', _('Avg')
        MINIMUM = 'min', _('Min')
        MAXIMUM = 'max', _('Max')

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
                                     choices=IntervalType.choices,
                                     default=IntervalType.HOUR
                                     )
    interval_count = models.IntegerField()
    num_channels = models.IntegerField()
    stat = models.CharField(max_length=8,
                            choices=Stat.choices,
                            default=Stat.SUM
                            )

    def calc_interval_seconds(self):
        '''Return the number of seconds in the alarm interval'''
        seconds = self.interval_count
        if self.interval_type == self.IntervalType.MINUTE:
            seconds *= 60
        elif self.interval_type == self.IntervalType.HOUR:
            seconds *= 60 * 60
        elif self.interval_type == self.IntervalType.DAY:
            seconds *= 60 * 60 * 24
        else:
            print('Invalid interval type!')
            return 0

        return seconds

    def agg_measurements(self, endtime=datetime.now(tz=pytz.UTC)):
        '''
        Gather all measurements for the alarm and calculate aggregate values
        '''
        seconds = self.calc_interval_seconds()
        starttime = endtime - timedelta(seconds=seconds)

        group = self.channel_group
        metric = self.metric

        # Get a QuerySet containing only measurements for the correct time
        # period and metric for this alarm
        q = metric.measurements.filter(starttime__range=(starttime, endtime),
                                       channel__in=group.channels.all())

        # Add extra filter for value__gt and/or value__lt?

        # Now calculate the aggregate values for each channel
        q = q.values('channel').annotate(count=Count('value'),
                                         sum=Sum('value'),
                                         avg=Avg('value'),
                                         max=Max('value'),
                                         min=Min('value'))

        return q

    def evaluate_alarm(self, endtime=datetime.now(tz=pytz.UTC)):
        '''
        Higher-level function that determines alarm state and calls other
        functions to create alerts if necessary
        '''
        # Get aggregate values for each channel. Returns a QuerySet
        channel_values = self.agg_measurements(endtime)

        # Get AlarmThresholds for this alarm. Returns a QuerySet
        alarm_thresholds = self.alarm_thresholds.all()

        # Evaluate whether each AlarmThreshold is breaching
        for alarm_threshold in alarm_thresholds:
            in_alarm = alarm_threshold.in_alarm_state(channel_values)
            alarm_threshold.evaluate_alert(in_alarm)

    def __str__(self):
        return (f"{str(self.channel_group)}, "
                f"{str(self.metric)}, "
                f"{self.interval_count} {self.interval_type}, "
                f"{self.num_channels} chan, "
                f"{self.stat}"
                )


class AlarmThreshold(MeasurementBase):
    '''Describe an individual alarm_threshold for an alarm'''

    # Define choices for interval_type
    class Level(models.IntegerChoices):
        ONE = 1
        TWO = 2
        THREE = 3

    alarm = models.ForeignKey(
        Alarm,
        on_delete=models.CASCADE,
        related_name='alarm_thresholds'
    )
    minval = models.FloatField(blank=True, null=True)
    maxval = models.FloatField(blank=True, null=True)
    band_inclusive = models.BooleanField(default=True)
    level = models.IntegerField(choices=Level.choices,
                                default=Level.ONE
                                )

    # channel_value is dict
    def is_breaching(self, channel_value):
        '''
        Determine if an individual aggregate channel value is breaching for
        this AlarmThreshold
        '''
        val = channel_value[self.alarm.stat]
        # check three cases: only minval, only maxval, both min and max
        if not self.minval and not self.maxval:
            print('minval or maxval should be defined!')
            return False
        elif self.minval and not self.maxval:
            return val < self.minval
        elif not self.minval and self.maxval:
            return val > self.maxval
        else:
            inside_band = (val > self.minval and val < self.maxval)
            return inside_band == self.band_inclusive

        # Shouldn't ever get here, but return False anyway
        return False

    # channel_values is QuerySet
    def get_breaching_channels(self, channel_values):
        '''Return all channels that are breaching this AlarmThreshold'''
        breaching_channels = []
        for channel_value in channel_values:
            if self.is_breaching(channel_value):
                breaching_channels.append(channel_value['channel'])

        return breaching_channels

    # channel_values is QuerySet
    def in_alarm_state(self, channel_values):
        '''
        Determine if AlarmThreshold is breaching for input aggregate channel
        values
        '''
        breaching_channels = self.get_breaching_channels(channel_values)
        return len(breaching_channels) >= self.alarm.num_channels

    def get_latest_alert(self):
        '''Return the most recent alert for this AlarmThreshold'''
        return self.alerts.order_by('timestamp').last()

    def get_alert_message(self, in_alarm):
        return 'This is an alert for ' + str(self.id)

    def create_alert(self, in_alarm):
        msg = self.get_alert_message(in_alarm)
        new_alert = Alert(alarm_threshold=self,
                          timestamp=datetime.now(tz=pytz.UTC),
                          message=msg,
                          in_alarm=in_alarm,
                          user=self.user)
        new_alert.save()
        Notification.create_alert_notifications(new_alert)
        return new_alert

    def evaluate_alert(self, in_alarm):
        '''
        Determine what to do with alerts given that this AlarmThreshold is in
        or out of spec
        '''
        alert = self.get_latest_alert()

        if in_alarm:
            # In alarm state, does alert exist yet? If not, create a new one.
            # Exist means the most recent one has in_alarm = True
            if not alert or not alert.in_alarm:
                return self.create_alert(in_alarm)
        else:
            # Not in alarm state, is there an alert to cancel?
            # If so, create new one saying in_alarm = False
            if alert and alert.in_alarm:
                return self.create_alert(in_alarm)

        return alert

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
                f"{str(self.alarm_threshold)}"
                )


class Archive(models.Model):
    """An archive-summary of measurements"""
    class ArchiveType(models.TextChoices):
        DAY = 'day', 'Day'
        WEEK = 'week', 'Week'
        MONTH = 'month', 'Month'

    archive_type = models.CharField(max_length=8, choices=ArchiveType.choices)
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
