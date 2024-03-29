from django.db import models
from django.db.models import (Avg, Count, Max, Min, Sum, F, Value,
                              IntegerField, FloatField)
from django.db.models.functions import Abs
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string

from measurement.aggregates.percentile import Percentile
from nslc.models import Channel, Group

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import operator
from measurement.fields import EmailListArrayField
import os

from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django.core.signing import Signer, BadSignature
from django.urls import reverse


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
        MINABS = 'minabs', _('MinAbs')
        MAXABS = 'maxabs', _('MaxAbs')
        MEDIAN = 'median', _('Median')
        P90 = 'p90', _('P90')
        P95 = 'p95', _('P95')

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
    do_daily_digest = models.BooleanField(default=False)

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

    def agg_measurements(self, endtime=None):
        '''
        Gather all measurements for the alarm and calculate aggregate values
        '''
        if not endtime:
            endtime = datetime.now(tz=pytz.UTC)
        group = self.channel_group
        metric = self.metric
        q_data = Measurement.objects.none()

        # q_list is returned to the caller
        q_list = []

        # Get a QuerySet containing only measurements for the correct time
        # period and metric for this alarm
        if self.interval_type == self.IntervalType.LASTN:
            # 10/27/23 CWU: Temporarily disable LASTN evaluation since it was
            # taking too many db resources
            return q_list

            # Special case that isn't time-based
            # Restrict time window to reduce query time
            starttime = endtime - timedelta(weeks=1)
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
            min=Min('value'),
            minabs=Min(Abs('value')),
            maxabs=Max(Abs('value')),
            median=Percentile('value', percentile=0.5),
            p90=Percentile('value', percentile=0.90),
            p95=Percentile('value', percentile=0.95)
        )

        # Get default values if there are no measurements
        q_default = group.channels.values(channel=F('id')).annotate(
            count=Value(0, output_field=IntegerField()),
            sum=Value(None, output_field=FloatField()),
            avg=Value(None, output_field=FloatField()),
            max=Value(None, output_field=FloatField()),
            min=Value(None, output_field=FloatField()),
            maxabs=Value(None, output_field=FloatField()),
            minabs=Value(None, output_field=FloatField()),
            median=Value(None, output_field=FloatField()),
            p90=Value(None, output_field=FloatField()),
            p95=Value(None, output_field=FloatField())
        )

        # Combine querysets in case of zero measurements. Kludgy but
        # shouldn't strain the db as much?
        q_dict = {obj['channel']: obj for obj in q_data}
        for chan_default in q_default:
            if chan_default['channel'] not in q_dict:
                q_list.append(chan_default)
            else:
                q_list.append(q_dict[chan_default['channel']])

        return q_list

    def evaluate_alarm(self,
                       endtime=None):
        '''
        Higher-level function that determines alarm state and calls other
        functions to create alerts if necessary. Default is to start on the
        hour regardless of when it is called (truncate down).
        '''
        if not endtime:
            endtime = datetime.now(tz=pytz.UTC) - relativedelta(
                minute=0, second=0, microsecond=0)

        # Get aggregate values for each channel. Returns a list(QuerySet)
        channel_values = self.agg_measurements(endtime)

        # Get Triggers for this alarm. Returns a QuerySet
        triggers = self.triggers.all()

        for trigger in triggers:
            breaching_channels = trigger.get_breaching_channels(channel_values)
            in_alarm = trigger.in_alarm_state(breaching_channels)
            trigger.evaluate_alert(in_alarm, breaching_channels, endtime)

        # Set the digest to be evaluated at this time. Should it be a field?
        digesttime = datetime.now(tz=pytz.UTC) - relativedelta(
            hour=0, minute=0, second=0, microsecond=0)
        endtimecheck = endtime - relativedelta(
            minute=0, second=0, microsecond=0)
        if self.do_daily_digest and endtimecheck == digesttime:
            self.check_daily_digest(digesttime)

    def check_daily_digest(self,
                           digesttime=None):
        if not digesttime:
            digesttime = datetime.now(tz=pytz.UTC)

        # Get the date string for yesterday
        yesterday_str = (
            digesttime - relativedelta(days=1)).strftime("%Y-%m-%d")

        triggers = self.triggers.all()
        # Get trigger contexts - information about the previous day
        trigger_contexts = []
        for trigger in triggers:
            trigger_contexts.append(
                trigger.get_daily_trigger_digest(digesttime))

        n_in_alert = sum([1 for res in trigger_contexts if res['in_alarm']])
        if n_in_alert == 0:
            # No alerts, no need to send digest
            return

        # Get emails for triggers that were in alarm
        emails = []
        for i, trigger in enumerate(triggers):
            if trigger_contexts[i]['in_alarm']:
                emails += [email for email in trigger.emails]

        if not emails:
            # There is noone specified to send to
            return

        context = get_monitor_context(self)
        context['yesterday'] = digesttime - relativedelta(days=1)
        context['n_in_alert'] = n_in_alert
        context['trigger_contexts'] = trigger_contexts

        # render email text
        email_html_message = render_to_string(
            'email/monitor_daily_digest.html', context)
        email_plaintext_message = render_to_string(
            'email/monitor_daily_digest.txt', context)

        subject = f"SQUAC daily digest for '{str(self)}'"
        subject += f", {yesterday_str}"
        send_mail(subject,
                  email_plaintext_message,
                  settings.EMAIL_NO_REPLY,
                  [email for email in emails],
                  fail_silently=False,
                  html_message=email_html_message
                  )

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

    emails = EmailListArrayField(models.EmailField(
        null=True, blank=True), null=True, blank=True)

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
                    self.monitor.stat: value,
                    "value": value
                })

        # Sort the channels for simplicity later
        breaching_channels = sorted(
            breaching_channels, key=lambda channel: channel['channel'])
        return breaching_channels

    def get_breaching_change(self,
                             breaching_channels,
                             reftime=None):
        '''
        Return channels that were added or removed from the previous
        breaching_channels list
        '''
        if not reftime:
            reftime = datetime.now(tz=pytz.UTC)

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
                       breaching_channels):
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

    def get_latest_alert(self, reftime=None):
        '''Return the most recent alert for this Trigger'''
        if not reftime:
            reftime = datetime.now(tz=pytz.UTC)

        return self.alerts.filter(
            timestamp__lte=reftime).order_by('timestamp').last()

    def create_alert(self,
                     in_alarm,
                     breaching_channels=[],
                     timestamp=None):
        if not timestamp:
            timestamp = datetime.now(tz=pytz.UTC)

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
                       reftime=None):
        '''
        Determine what to do with alerts given that this Trigger is in
        or out of spec
        '''
        if not reftime:
            reftime = datetime.now(tz=pytz.UTC)
        alert = self.get_latest_alert(reftime=reftime)
        create_new = False
        send_new = False

        # Create alert whenever in alarm or when exiting alarm state
        if in_alarm:
            # always create an alert when in alarm
            create_new = True

            # if last alert does not exist or was not in alarm, send new one
            if not alert or not alert.in_alarm:
                send_new = True
        else:
            # Not in alarm state, is there an alert to cancel?
            # If so, create new one saying in_alarm = False
            if alert and alert.in_alarm:
                create_new, send_new = True, self.alert_on_out_of_alarm

        if self.num_channels_operator == self.NumChannelsOperator.ANY:
            # Special treatment for num_channels_operator == ANY
            added, removed = self.get_breaching_change(
                breaching_channels, reftime)
            if added:
                # Always send new alert if new channels are added
                send_new = True
            elif removed:
                send_new = self.alert_on_out_of_alarm

        # Make sure to not send individual alerts if daily digest is on.
        # They can still be created
        if self.monitor.do_daily_digest:
            send_new = False

        if create_new:
            alert = self.create_alert(in_alarm,
                                      breaching_channels=breaching_channels,
                                      timestamp=reftime)
            if send_new:
                alert.send_alert()

        return alert

    def get_text_description(self, verbose=True):
        '''
        Try to return something like:
            Alert if avg of hourly_mean measurements is outside of (-5, 5)
            for less than 5 channels in channel group: UW SMAs
            over the last 5 hours
        see https://github.com/pnsn/squacapi/issues/373
        '''
        # Handle num_channels differently
        if self.num_channels_operator == self.NumChannelsOperator.ANY:
            num_channels_description = 'ANY'
            # manually set num channels to get correct pluralization
            num_channels = 1
        elif self.num_channels_operator == self.NumChannelsOperator.ALL:
            num_channels_description = 'ALL'
            # manually set num channels to get correct pluralization
            num_channels = 2
        else:
            num_channels_description = (
                f'{self.num_channels_operator} {self.num_channels}')
            num_channels = self.num_channels

        # Create context to send to render_to_string. Could move some of this
        # logic to the template and send a dict of this instance instead
        context = {
            'value': (
                (self.val1, self.val2) if self.val2 is not None
                else self.val1),
            'stat': self.monitor.stat,
            'metric_name': self.monitor.metric.name,
            'value_operator': self.value_operator,
            'num_channels_description': num_channels_description,
            'num_channels_operator': self.num_channels_operator,
            'num_channels': num_channels,
            'channel_group': self.monitor.channel_group,
            'interval_count': self.monitor.interval_count,
            'interval_type': (
                'latest value'
                if operator.eq(self.monitor.interval_type,
                               self.monitor.IntervalType.LASTN)
                else self.monitor.interval_type),
        }

        if verbose:
            trigger_description = render_to_string(
                'monitors/trigger_description_verbose.txt', context)
        else:
            trigger_description = render_to_string(
                'monitors/trigger_description_simple.txt', context)

        return trigger_description

    def get_daily_trigger_digest(self, digesttime):
        """
        digesttime is the time this is evaluated. So the code will actually
        check what happened the day before.

        Return boolean of whether this trigger was in alarm today
        Then text description:
        - At top should be brief trigger description
        - Then summary of alerts for the day
        - Then breaching channels, including breaching since times
        """
        # trigger_context will be returned and ultimately used in crafting the
        # digest email
        trigger_context = {
            'in_alarm': False,
            'trigger_description': self.get_text_description(verbose=False),
            'unsubscribe_url': self.create_unsubscribe_url()
        }

        # Use check time to ensure digesttime is 00:00, and the trigger will be
        # evaluated for the day before
        checktime = digesttime - relativedelta(
            hour=0, minute=0, second=0, microsecond=0)
        alerts = self.alerts.filter(
            timestamp__gte=checktime - relativedelta(days=1),
            timestamp__lte=checktime).order_by('timestamp')

        # If there were no alerts today, return now.
        if len(alerts) == 0:
            return trigger_context

        # There were alerts, so categorize them and generate a summary
        in_alarm_times = [
            alert.timestamp.strftime('%H:%M') for alert in alerts
            if alert.in_alarm
        ]
        out_of_alarm_times = [
            alert.timestamp.strftime('%H:%M') for alert in alerts
            if not alert.in_alarm
        ]

        # Now add the list of breaching channels (first generate it)
        channels_dict = {}
        for alert in alerts:
            for channel in alert.breaching_channels:
                # Keep track of the most recent breaching time per channel
                channels_dict[channel['channel']] = alert.timestamp

        # Sort the channels by NSLC
        channels_list = []
        for channel_name in sorted(channels_dict.keys()):
            channels_list.append({
                'channel': channel_name,
                'timestamp': channels_dict[channel_name]
            })

        trigger_context['in_alarm'] = True
        trigger_context['in_alarm_times'] = in_alarm_times
        trigger_context['out_of_alarm_times'] = out_of_alarm_times
        trigger_context['breaching_channels'] = channels_list

        return trigger_context

    def create_unsubscribe_url(self):
        ''' creates a link to the unsubscribe url for given trigger'''
        token = self.make_token()
        return reverse('measurement:trigger-unsubscribe',
                       kwargs={'pk': self.pk, 'token': token})

    def make_token(self):
        ''' generates a token for the given id'''
        id, token = Signer().sign(self.pk).split(":", 1)
        return token

    def check_token(self, token):
        ''' validates that the given token matches the trigger'''
        try:
            key = '%s:%s' % (self.pk, token)

            Signer().unsign(key)
        except BadSignature:
            return False
        return True

    def unsubscribe(self, email):
        ''' removes given email from the trigger's emails '''
        if self.emails and email in self.emails:
            self.emails.remove(email)
            self.save(update_fields=['emails'])

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

    def send_alert(self):
        if not self.trigger.emails:
            # There is noone specified to send to
            return False
        in_out = "IN" if self.in_alarm else "OUT OF"
        subject = f"SQUAC {in_out} alert for '{self.trigger.monitor}'"
        added, removed = None, None
        if operator.eq(self.trigger.num_channels_operator,
                       Trigger.NumChannelsOperator.ANY):
            # Use one second before as reftime just to make sure this alert
            # itself isn't used as the latest alert
            added, removed = self.trigger.get_breaching_change(
                self.breaching_channels,
                self.timestamp - timedelta(seconds=1))

        # could send just trigger to simplify this, but then the
        # HTML is more complex
        context = get_monitor_context(self.trigger.monitor)
        context["timestamp"] = self.timestamp
        context["in_out"] = in_out
        context["unsubscribe_url"] = remote_host(
        ) + self.trigger.create_unsubscribe_url()
        context["trigger"] = self.trigger
        context["added_channels"] = added
        context["removed_channels"] = removed
        context["breaching_channels"] = self.breaching_channels
        context["trigger_description"] = self.trigger.get_text_description(
            verbose=False),

        # render email text
        email_html_message = render_to_string(
            'email/alert_email.html', context)

        email_plaintext_message = render_to_string(
            'email/alert_email.txt', context)

        send_mail(subject,
                  email_plaintext_message,
                  settings.EMAIL_NO_REPLY,
                  [email for email in self.trigger.emails],
                  fail_silently=False,
                  html_message=email_html_message
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

    @property
    def sum(self):
        return (self.mean * self.num_samps)

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


def remote_host():
    # Determine the base url
    env = os.environ.get('SQUAC_ENVIRONMENT')
    if env == 'production':
        remote_host = "https://squac.pnsn.org"
    elif env == 'staging':
        remote_host = "https://staging-squac.pnsn.org"
    elif env == 'localhost':
        remote_host = "localhost:8000"
    else:
        remote_host = "http://squac.pnsn.org"

    return remote_host


def get_monitor_context(monitor):
    """ Monitor context for emails that is shared """
    host = remote_host()
    return {
        'now': datetime.now(tz=pytz.UTC),
        'remote_host': host,
        'channel_group': monitor.channel_group,
        'name': monitor.name,
        'metric': monitor.metric.name,
        'stat': monitor.stat,
        'interval_count': monitor.interval_count,
        'interval_type': (
            'latest value'
            if (monitor.interval_type == monitor.IntervalType.LASTN)
            else monitor.interval_type),
        'monitor_url': "{}/{}/{}".format(
            host, "monitors", monitor.id),
        'channel_group_url': "{}/{}/{}".format(
            host, "channel-groups", monitor.channel_group.id),
        'metric_url': "{}/{}/{}".format(
            host, "metrics", monitor.metric.id)
    }
