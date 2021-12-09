from django.db import models
from django.db.models import (Avg, Count, Max, Min, Sum, F, Value,
                              IntegerField, FloatField)
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from dashboard.models import Widget
from nslc.models import Channel, Group

from datetime import datetime, timedelta
import pytz

from bulk_update_or_create import BulkUpdateOrCreateQuerySet


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
    sample_rate = models.IntegerField(default=3600)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]


class Measurement(MeasurementBase):
    '''describes the observable metrics'''
    objects = BulkUpdateOrCreateQuerySet.as_manager()
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

    def __str__(self):
        return (f"Threshold for Widget: {str(self.widget)} "
                f"Metric: {str(self.metric)}"
                f"Min {self.minval}"
                f"Max {self.maxval}"
                )


class Monitor(MeasurementBase):
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
        related_name='monitors'
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='monitors'
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
    name = models.CharField(max_length=255, default='')
    invert_monitor = models.BooleanField(default=False)
    # Either (or both) of the alert_for_channel... options would make
    # num_channels and invert_monitor irrelevant. Now only alert if any channel
    # joins or drops out of the breaching_channels list for a trigger/alert
    alert_for_channel_added = models.BooleanField(default=False)
    alert_for_channel_removed = models.BooleanField(default=False)

    @property
    def alert_for_single(self):
        return self.alert_for_channel_added or self.alert_for_channel_removed

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
        q_data = metric.measurements.filter(
            starttime__range=(starttime, endtime),
            channel__in=group.channels.all()
        )

        # Now calculate the aggregate values for each channel
        q_data = q_data.values('channel').annotate(
            count=Count('value'),
            sum=Sum('value'),
            avg=Avg('value'),
            max=Max('value'),
            min=Min('value')
        )

        # Get default values if there are no measurements
        q_default = group.channels.values(channel=F('id')).annotate(
            count=Value(0, output_field=IntegerField()),
            sum=Value(None, output_field=FloatField()),
            avg=Value(None, output_field=FloatField()),
            max=Value(None, output_field=FloatField()),
            min=Value(None, output_field=FloatField())
        )

        # Combine querysets in case of zero measurements. Kludgy but
        # shouldn't strain the db as much?
        q_dict = {obj['channel']: obj for obj in q_data}
        q_list = []
        for chan_default in q_default:
            if chan_default['channel'] not in q_dict:
                q_list.append(chan_default)
            else:
                q_list.append(q_dict[chan_default['channel']])

        return q_list

    def evaluate_alarm(self, endtime=datetime.now(tz=pytz.UTC)):
        '''
        Higher-level function that determines alarm state and calls other
        functions to create alerts if necessary
        '''
        # Get aggregate values for each channel. Returns a list(QuerySet)
        channel_values = self.agg_measurements(endtime)

        # Get Triggers for this alarm. Returns a QuerySet
        triggers = self.triggers.all()

        # Evaluate whether each Trigger is breaching
        for trigger in triggers:
            in_alarm, breaching_channels = (
                trigger.in_alarm_state(channel_values))
            trigger.evaluate_alert(in_alarm, breaching_channels, endtime)

    def __str__(self):
        if not self.name:
            return (f"{str(self.channel_group)}, "
                    f"{str(self.metric)}, "
                    f"{self.interval_count} {self.interval_type}, "
                    f"{self.num_channels} chan, "
                    f"{self.stat}"
                    )
        else:
            return self.name


class Trigger(MeasurementBase):
    '''Describe an individual trigger for a monitor'''

    # Define choices for notification level
    class Level(models.IntegerChoices):
        ONE = 1
        TWO = 2
        THREE = 3

    monitor = models.ForeignKey(
        Monitor,
        on_delete=models.CASCADE,
        related_name='triggers'
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
        this Trigger
        '''
        val = channel_value[self.monitor.stat]
        # if val is None that means there were zero measurements for this
        # metric during the given time period
        if val is None:
            return False

        # check three cases: only minval, only maxval, both min and max
        if self.minval is None and self.maxval is None:
            return False
        elif self.minval is not None and self.maxval is None:
            return val < self.minval
        elif self.minval is None and self.maxval is not None:
            return val > self.maxval
        else:
            inside_band = (val > self.minval and val < self.maxval)
            return inside_band == self.band_inclusive

        # Shouldn't ever get here, but return False anyway
        return False

    # channel_values is a list of dicts
    def get_breaching_channels(self, channel_values):
        '''Return all channels that are breaching this Trigger'''
        breaching_channels = []
        for channel_value in channel_values:
            if self.is_breaching(channel_value):
                channel = Channel.objects.filter(id=channel_value['channel'])
                # Should just be one channel in the filter queryset
                if len(channel) != 1:
                    continue

                value = channel_value[self.monitor.stat]
                breaching_channels.append({
                    'channel': str(channel[0]),
                    'channel_id': channel_value['channel'],
                    self.monitor.stat: value
                })

        return breaching_channels

    def get_breaching_change(self,
                             breaching_channels,
                             reftime=datetime.now(tz=pytz.UTC)):
        '''
        Return channels that were added or removed from the previous
        breaching_channels list
        '''
        added = []
        removed = []
        alert = self.get_latest_alert(reftime)
        if alert:
            previous_ids = {x['channel_id'] for x in alert.breaching_channels}
            current_ids = {x['channel_id'] for x in breaching_channels}
            for chan in breaching_channels:
                if chan['channel_id'] not in previous_ids:
                    added.append(chan)
            for chan in alert.breaching_channels:
                if chan['channel_id'] not in current_ids:
                    removed.append(chan)
        else:
            # Case where there was no previous alert
            added = breaching_channels

        return added, removed

    # channel_values is a list of dicts
    def in_alarm_state(self, channel_values):
        '''
        Determine if Trigger is breaching for input aggregate channel
        values
        '''
        breaching_channels = self.get_breaching_channels(channel_values)
        if self.monitor.alert_for_single:
            # Case alert_for_channel_added or alert_for_channel_removed
            added, removed = self.get_breaching_change(breaching_channels)
            if self.monitor.alert_for_channel_added and added:
                return True, breaching_channels
            if self.monitor.alert_for_channel_removed and removed:
                return True, breaching_channels
            return False, breaching_channels
        else:
            if self.monitor.invert_monitor:
                return (len(breaching_channels) < self.monitor.num_channels,
                        breaching_channels)
            else:
                return (len(breaching_channels) >= self.monitor.num_channels,
                        breaching_channels)

    def get_latest_alert(self, reftime=datetime.now(tz=pytz.UTC)):
        '''
        Return the most recent alert for this Trigger relative to the
        given time
        '''
        return self.alerts.filter(timestamp__lt=reftime
                                  ).order_by('timestamp').last()

    def create_alert(self,
                     in_alarm,
                     breaching_channels=[],
                     timestamp=datetime.now(tz=pytz.UTC)):
        new_alert = Alert(trigger=self,
                          timestamp=timestamp,
                          message="",
                          in_alarm=in_alarm,
                          user=self.user,
                          breaching_channels=breaching_channels)
        new_alert.save()
        new_alert.create_alert_notifications()
        return new_alert

    def evaluate_alert(self,
                       in_alarm,
                       breaching_channels=[],
                       reftime=datetime.now(tz=pytz.UTC)):
        '''
        Determine what to do with alerts given that this Trigger is in
        or out of spec
        '''
        if self.monitor.alert_for_single:
            # Special treatment for this case. It could alert because of a
            # single channel being added or removed from breaching_channels
            if in_alarm:
                return self.create_alert(in_alarm, breaching_channels, reftime)

        # "Normal" case for the rest of the method
        alert = self.get_latest_alert(reftime)

        if in_alarm:
            # In alarm state, does alert exist yet? If not, create a new one.
            # Exist means the most recent one has in_alarm = True
            if not alert or not alert.in_alarm:
                return self.create_alert(in_alarm, breaching_channels, reftime)
        else:
            # Not in alarm state, is there an alert to cancel?
            # If so, create new one saying in_alarm = False
            if alert and alert.in_alarm:
                return self.create_alert(in_alarm, breaching_channels, reftime)

        return alert

    def __str__(self):
        return (f"Monitor: {str(self.monitor)}, "
                f"Min: {self.minval}, "
                f"Max: {self.maxval}, "
                f"Level: {self.level}"
                )


class Alert(MeasurementBase):
    '''Describe an alert for a trigger'''
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    timestamp = models.DateTimeField()
    message = models.CharField(max_length=255)
    in_alarm = models.BooleanField(default=True)
    breaching_channels = models.JSONField(null=True)

    def create_alert_notifications(self):
        level = self.trigger.level
        notifications = self.user.get_notifications(level)

        for notification in notifications:
            notification.send(self)

    def get_printable_channel(self, channel, include_stat=True):
        no_include = ['channel_id']
        if not include_stat:
            no_include += ([x[0] for x in Monitor.Stat.choices])

        return str({k: v for k, v in channel.items() if k not in no_include})

    def get_printable_channels(self, channels, include_stat=True):
        if not channels:
            return ''
        str_out = '\n[\n'
        for channel in channels:
            str_out += self.get_printable_channel(channel, include_stat)
            str_out += ',\n'

        return str_out + ']'

    def get_email_message(self):
        msg = ''
        if self.trigger.monitor.alert_for_single:
            msg += 'Trigger alert for ' + str(self.trigger)
            added, removed = self.trigger.get_breaching_change(
                self.breaching_channels, self.timestamp)
            if self.trigger.monitor.alert_for_channel_added and added:
                added_out = self.get_printable_channels(added)
                msg += '\nNew channels in alert: ' + str(added_out)
            if self.trigger.monitor.alert_for_channel_removed and removed:
                removed_out = self.get_printable_channels(removed,
                                                          include_stat=False)
                msg += '\nNew channels out of alert: ' + str(removed_out)
        else:
            if self.in_alarm:
                msg += 'Trigger in alert for ' + str(self.trigger)
            else:
                msg += 'Trigger out of alert for ' + str(self.trigger)

        breaching_out = self.get_printable_channels(self.breaching_channels)
        msg += '\nAll breaching channels: ' + str(breaching_out)
        return msg

    class Meta:
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return (f"Time: {self.timestamp}, "
                f"{str(self.trigger)}"
                )


class ArchiveBase(models.Model):
    """An archive-summary of measurements"""
    class Meta:
        abstract = True
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-starttime']),
        ]

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    min = models.FloatField()
    max = models.FloatField()
    mean = models.FloatField()
    median = models.FloatField()
    stdev = models.FloatField()
    num_samps = models.IntegerField()
    p05 = models.FloatField()
    p10 = models.FloatField()
    p90 = models.FloatField()
    p95 = models.FloatField()
    starttime = models.DateTimeField(auto_now=False)
    endtime = models.DateTimeField(auto_now=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def minabs(self):
        return min(abs(self.min), abs(self.max))

    @property
    def maxabs(self):
        return max(abs(self.min), abs(self.max))

    def __str__(self):
        return (f"Archive of Metric: {str(self.metric)} "
                f"Channel: {str(self.channel)} "
                f"from {format(self.starttime, '%m-%d-%Y')} "
                f"to {format(self.endtime, '%m-%d-%Y')}")


class ArchiveHour(ArchiveBase):
    pass


class ArchiveDay(ArchiveBase):
    pass


class ArchiveWeek(ArchiveBase):
    pass


class ArchiveMonth(ArchiveBase):
    pass
