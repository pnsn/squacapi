from django.db import models
from django.db.models import (Avg, Count, Max, Min, Sum, F, Value,
                              IntegerField, FloatField)
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from .validators import validate_email_list
from nslc.models import Channel, Group

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import operator

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
                f"starttime: {format(self.starttime, '%m-%d-%Y %H:%M:%S')} "
                f"endtime: {format(self.endtime, '%m-%d-%Y %H:%M:%S')} "
                )


class Monitor(MeasurementBase):
    '''Describes alarms on metrics and channel_groups'''

    # Define choices for interval_type
    class IntervalType(models.TextChoices):
        MINUTE = 'minute', _('Minute')
        HOUR = 'hour', _('Hour')
        DAY = 'day', _('Day')
        LASTN = 'last n', _('Last N')

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
    interval_type = models.CharField(
        max_length=8,
        choices=IntervalType.choices,
        default=IntervalType.HOUR
    )
    interval_count = models.IntegerField()
    stat = models.CharField(
        max_length=8,
        choices=Stat.choices,
        default=Stat.SUM
    )
    name = models.CharField(max_length=255, default='')

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
        group = self.channel_group
        metric = self.metric
        q_data = Measurement.objects.none()

        # Get a QuerySet containing only measurements for the correct time
        # period and metric for this alarm
        if self.interval_type == self.IntervalType.LASTN:
            # Special case that isn't time-based
            # Restrict time window to reduce query time
            starttime = endtime - timedelta(weeks=2)
            measurement_ids = []
            for channel in group.channels.all():
                measurements = metric.measurements.filter(
                    starttime__range=(starttime, endtime),
                    channel=channel
                ).order_by(
                    '-starttime')[:self.interval_count]
                measurement_ids += list(
                    measurements.values_list('id', flat=True)
                )

            q_data = Measurement.objects.filter(id__in=measurement_ids)
        else:
            seconds = self.calc_interval_seconds()
            starttime = endtime - timedelta(seconds=seconds)
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

    def evaluate_alarm(self, endtime=datetime.now(tz=pytz.UTC) - relativedelta(
                       minute=0, second=0, microsecond=0)):
        '''
        Higher-level function that determines alarm state and calls other
        functions to create alerts if necessary. Default is to start on the
        hour regardless of when it is called (truncate down).
        '''
        # Get aggregate values for each channel. Returns a list(QuerySet)
        channel_values = self.agg_measurements(endtime)

        # Get Triggers for this alarm. Returns a QuerySet
        triggers = self.triggers.all()

        for trigger in triggers:
            breaching_channels = trigger.get_breaching_channels(channel_values)
            in_alarm = trigger.in_alarm_state(breaching_channels, endtime)
            trigger.evaluate_alert(in_alarm, breaching_channels, endtime)

    def __str__(self):
        if not self.name:
            return (f"{str(self.channel_group)}, "
                    f"{str(self.metric)}, "
                    f"{self.interval_count} {self.interval_type}, "
                    f"{self.stat}"
                    )
        else:
            return self.name

    def save(self, *args, **kwargs):
        """
        Reset alerts associated with triggers on this monitor
        """
        super().save(*args, **kwargs)  # Call the "real" save() method.

        for trigger in self.triggers.all():
            trigger.create_alert(False)


class Trigger(MeasurementBase):
    '''Describe an individual trigger for a monitor'''

    class ValueOperator(models.TextChoices):
        '''
        How to compare calculated value to val1 (and val2) threshold to
        determine if a channel is breaching
        '''
        OUTSIDE_OF = 'outsideof', _('Outside of')
        WITHIN = 'within', _('Within')
        EQUAL_TO = '==', _('Equal to')
        LESS_THAN = '<', _('Less than')
        LESS_THAN_OR_EQUAL = '<=', _('Less than or equal to')
        GREATER_THAN = '>', _('Greater than')
        GREATER_THAN_OR_EQUAL = '>=', _('Greater than or equal to')

    class NumChannelsOperator(models.TextChoices):
        '''
        How to compare num_channels to breaching channels to determine if
        trigger is in alarm
        '''
        ANY = 'any', _('Any')
        ALL = 'all', _('All')
        EQUAL_TO = '==', _('Equal to')
        LESS_THAN = '<', _('Less than')
        GREATER_THAN = '>', _('Greater than')

    OPERATOR = {
        '==': operator.eq,
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge
    }

    monitor = models.ForeignKey(
        Monitor,
        on_delete=models.CASCADE,
        related_name='triggers'
    )
    '''
    val1 is required. It acts as minval when value_operator is OUTSIDE_OF
    or WITHIN. Otherwise it is used for single value comparisons.
    '''
    val1 = models.FloatField()
    '''
    val2 is optional. It is used as maxval when value_operator is OUTSIDE_OF
    or WITHIN. Otherwise it is ignored.
    '''
    val2 = models.FloatField(blank=True, null=True)
    value_operator = models.CharField(
        max_length=16,
        choices=ValueOperator.choices,
        default=ValueOperator.GREATER_THAN
    )
    num_channels = models.IntegerField(blank=True, null=True)
    num_channels_operator = models.CharField(
        max_length=16,
        choices=NumChannelsOperator.choices,
        default=NumChannelsOperator.GREATER_THAN
    )
    alert_on_out_of_alarm = models.BooleanField(default=False)
    email_list = models.JSONField(blank=True,
                                  null=True,
                                  validators=[validate_email_list, ])

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

        if self.value_operator == self.ValueOperator.OUTSIDE_OF:
            return val < self.val1 or val > self.val2
        elif self.value_operator == self.ValueOperator.WITHIN:
            return val > self.val1 and val < self.val2
        else:
            return self.OPERATOR[self.value_operator](val, self.val1)

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

    # breaching_channels is a list of dicts from
    # trigger.get_breaching_channels()
    def in_alarm_state(self,
                       breaching_channels,
                       reftime=datetime.now(tz=pytz.UTC)):
        '''
        Determine if Trigger is in or out of alarm based on breaching_channels
        and num_channels_operator.
        '''
        if self.num_channels_operator == self.NumChannelsOperator.ANY:
            # This is a special case. evaluate_alert() will perform further
            # logic checks. Will always be "in_alarm" if there are more than
            # zero breaching channels
            return len(breaching_channels) > 0
        elif self.num_channels_operator == self.NumChannelsOperator.ALL:
            total_channels = self.monitor.channel_group.channels.count()
            return len(breaching_channels) == total_channels
        else:
            # Otherwise just compare the breaching_channels to the
            # num_channels_operator (>, ==, <)
            op = self.OPERATOR[self.num_channels_operator]
            return op(len(breaching_channels), self.num_channels)

    def get_latest_alert(self, reftime=datetime.now(tz=pytz.UTC)):
        '''Return the most recent alert for this Trigger'''
        return self.alerts.filter(
            timestamp__lte=reftime).order_by('timestamp').last()

    def create_alert(self,
                     in_alarm,
                     breaching_channels=[],
                     timestamp=datetime.now(tz=pytz.UTC)):
        new_alert = Alert(trigger=self,
                          timestamp=timestamp,
                          in_alarm=in_alarm,
                          user=self.user,
                          breaching_channels=breaching_channels)
        new_alert.save()
        return new_alert

    def evaluate_alert(self,
                       in_alarm,
                       breaching_channels=[],
                       reftime=datetime.now(tz=pytz.UTC)):
        '''
        Determine what to do with alerts given that this Trigger is in
        or out of spec
        '''
        alert = self.get_latest_alert()
        create_new = False
        send_new = False

        if self.num_channels_operator == self.NumChannelsOperator.ANY:
            # Special treatment for num_channels_operator == ANY
            added, removed = self.get_breaching_change(
                breaching_channels, reftime)
            if added:
                # Always send new alert if new channels are added
                create_new, send_new = True, True
            elif removed:
                create_new, send_new = True, self.alert_on_out_of_alarm
        else:
            # Regular treatment for num_channels_operator != ANY
            if in_alarm:
                # In alarm state, does alert exist yet? If not, create a new
                # one. Exist means the most recent one has in_alarm = True
                if not alert or not alert.in_alarm:
                    create_new, send_new = True, True
            else:
                # Not in alarm state, is there an alert to cancel?
                # If so, create new one saying in_alarm = False
                if alert and alert.in_alarm:
                    create_new, send_new = True, self.alert_on_out_of_alarm

        if create_new:
            alert = self.create_alert(in_alarm, breaching_channels, reftime)
            if send_new:
                alert.send_alert()

        return alert

    def get_text_description(self):
        '''
        Try to return something like:
            Alert if avg of hourly_mean measurements is outside of (-5, 5)
            for less than 5 channels in channel group: UW SMAs
            over the last 5 hours
        see https://github.com/pnsn/squacapi/issues/373
        '''
        desc = ''
        desc += f'Alert if {self.monitor.stat} of'
        desc += f' {self.monitor.metric.name} measurements'
        val = (self.val1, self.val2) if self.val2 is not None else self.val1
        desc += f' is {self.value_operator} {val}'
        if self.num_channels_operator == self.NumChannelsOperator.ANY:
            desc += '\n\nfor ANY channel'
        elif self.num_channels_operator == self.NumChannelsOperator.ALL:
            desc += '\n\nfor ALL channels'
        else:
            desc += f'\n\nfor {self.num_channels_operator} than'
            add_s = 's' if self.num_channels > 1 else ''
            desc += f' {self.num_channels} channel{add_s}'
        desc += f' in channel group: {self.monitor.channel_group}'
        add_s = 's' if self.monitor.interval_count > 1 else ''
        desc += f'\n\nover the last {self.monitor.interval_count}'
        desc += f' {self.monitor.interval_type}{add_s}'
        return desc

    def __str__(self):
        return (f"Monitor: {str(self.monitor)}, "
                f"Val1: {self.val1}, "
                f"Val2: {self.val2}"
                )

    def clean(self):
        """
        Some custom logic to make sure various fields correspond correctly
        """
        # Don't allow val2 to be None if using Within, OutsideOf
        if all([self.val2 is None,
                self.value_operator in (self.ValueOperator.WITHIN,
                                        self.ValueOperator.OUTSIDE_OF)]):
            raise ValidationError(
                _(f'val2 must be defined when using {self.value_operator}'))
        # If it is to be used, val2 must be greater than val1
        if self.val2 is not None and self.val1 > self.val2:
            raise ValidationError(
                _('val2 must be greater than val1'))
        # Don't allow num_channels to be None if not using ANY or ALL
        if all([self.num_channels is None,
                self.num_channels_operator != self.NumChannelsOperator.ANY,
                self.num_channels_operator != self.NumChannelsOperator.ALL]):
            raise ValidationError(
                _('num_channels must be defined when using'
                  f' {self.num_channels_operator}'))
        # Make sure email_list is an actual list
        if isinstance(self.email_list, str):
            self.email_list = [self.email_list]

    def save(self, *args, **kwargs):
        """
        Do regular save except also validate fields. This doesn't happen
        automatically on save. Also reset alerts associated with this trigger
        """
        # Validate fields
        try:
            self.full_clean()
        except ValidationError:
            raise

        super().save(*args, **kwargs)  # Call the "real" save() method.

        # Create a new alert with in_alarm = False. Should happen after trigger
        # is saved
        self.create_alert(False)


class Alert(MeasurementBase):
    '''Describe an alert for a trigger'''
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    timestamp = models.DateTimeField()
    in_alarm = models.BooleanField(default=True)
    breaching_channels = models.JSONField(null=True)

    def get_printable_channel(self, channel, include_stat=True):
        ret = str(channel['channel'])
        # The monitor stat should be a key
        stat = self.trigger.monitor.stat
        if stat in channel and include_stat:
            ret += f', {stat}: {channel[stat]}'

        return ret

    def get_printable_channels(self, channels, include_stat=True):
        str_out = ''
        if not channels:
            return str_out

        for channel in channels:
            str_out += '\n' + self.get_printable_channel(channel, include_stat)

        return str_out

    def get_email_message(self):
        msg = ''
        msg += self.timestamp.strftime('%Y-%m-%dT%H:%M %Z')
        in_out = 'IN' if self.in_alarm else 'OUT OF'
        msg += f'\n\nTrigger {in_out} alert for {str(self.trigger.monitor)}'
        msg += f'\n\n{self.trigger.get_text_description()}'

        if operator.eq(self.trigger.num_channels_operator,
                       Trigger.NumChannelsOperator.ANY):
            # Use one second before as reftime just to make sure this alert
            # itself isn't used as the latest alert
            added, removed = self.trigger.get_breaching_change(
                self.breaching_channels,
                self.timestamp - timedelta(seconds=1))
            if added:
                added_out = self.get_printable_channels(added)
                msg += '\n\nNew channels in alert:' + str(added_out)
            if removed:
                removed_out = self.get_printable_channels(removed, False)
                msg += '\n\nNew channels out of alert:' + str(removed_out)

        breaching_out = self.get_printable_channels(self.breaching_channels)
        msg += '\n\nAll breaching channels:' + str(breaching_out)
        return msg

    def send_alert(self):
        if not self.trigger.email_list:
            # There is noone specified to send to
            return False
        in_out = "IN" if self.in_alarm else "OUT OF"
        subject = f"SQUAC {in_out} alert for '{self.trigger.monitor}'"
        message = self.get_email_message()
        send_mail(subject,
                  message,
                  settings.EMAIL_NO_REPLY,
                  [email for email in self.trigger.email_list],
                  fail_silently=False,
                  )
        return True

    class Meta:
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return (f"in_alarm: {self.in_alarm}, "
                f"Time: {self.timestamp}, "
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
