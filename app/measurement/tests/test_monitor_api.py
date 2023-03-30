from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# from django.db.models import Avg, Count, Max, Min, Sum

from measurement.models import (Monitor, Trigger, Alert, Measurement,
                                Metric)
from nslc.models import Channel, Group, Network
from organization.models import Organization

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from squac.test_mixins import sample_user

'''Tests for monitor and trigger models:
to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    "./mg.sh "test measurement.tests.test_monitor_api && flake8"

'''


class PrivateMonitorApiTests(TestCase):
    '''For authenticated tests in alarms API

        Authenticate and make user admin so we are only testing
        routes and methods
    '''
    # More data to test filtering for alarm calculations
    fixtures = ['alarms.json']

    def getTestChannel(self, station_code):
        return Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code=station_code,
            station_name='Test Name',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )

    def getTestMonitor(self, interval_type=Monitor.IntervalType.MINUTE,
                       interval_count=2):
        return Monitor.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=interval_type,
            interval_count=interval_count,
            stat=Monitor.Stat.SUM,
            user=self.user
        )

    def getTestMeasurement(self, metric, channel, val, delta):
        basetime = datetime(2019, 5, 5, 8, 8, 7, 0, tzinfo=pytz.UTC)
        return Measurement.objects.create(
            metric=metric,
            channel=channel,
            value=val,
            starttime=basetime + delta,
            endtime=basetime + delta,
            user=self.user
        )

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.user.is_staff = True
        self.client.force_authenticate(self.user)
        timezone.now()
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.chan1 = self.getTestChannel('CH1')
        self.chan2 = self.getTestChannel('CH2')
        # self.chan3 = self.getTestChannel('CH3')
        self.grp = Group.objects.create(
            name='Test group',
            user=self.user,
            organization=self.organization,
        )
        self.grp.channels.set([self.chan1.id, self.chan2.id])
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            code="someotherthing",
            default_minval=1,
            default_maxval=10.0,
            user=self.user,
            reference_url='pnsn.org'
        )
        self.monitor = Monitor.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=Monitor.IntervalType.DAY,
            interval_count=1,
            stat=Monitor.Stat.SUM,
            user=self.user
        )
        self.trigger = Trigger.objects.create(
            monitor=self.monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[self.user.email]
        )
        self.alert = Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            in_alarm=True,
            user=self.user
        )

    def test_get_monitor(self):
        url = reverse(
            'measurement:monitor-detail',
            kwargs={'pk': self.monitor.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['interval_type'], Monitor.IntervalType.DAY)

    def test_get_monitor_includes_triggers(self):
        url = reverse(
            'measurement:monitor-detail',
            kwargs={'pk': 1}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # There are 5 triggers keyed to this monitor in fixture alarms.json
        self.assertEqual(5, len(res.data['triggers']))

    def test_create_monitor(self):
        url = reverse('measurement:monitor-list')
        payload = {
            'channel_group': self.grp.id,
            'metric': self.metric.id,
            'interval_type': Monitor.IntervalType.MINUTE,
            'interval_count': 5,
            'stat': Monitor.Stat.SUM,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        monitor = Monitor.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'channel_group':
                self.assertEqual(payload[key], monitor.channel_group.id)
            elif key == 'metric':
                self.assertEqual(payload[key], monitor.metric.id)
            else:
                self.assertEqual(payload[key], getattr(monitor, key))

    def test_get_trigger(self):
        url = reverse(
            'measurement:trigger-detail',
            kwargs={'pk': self.trigger.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['monitor'], self.monitor.id)

    def test_create_trigger(self):
        url = reverse('measurement:trigger-list')
        payload = {
            'monitor': self.monitor.id,
            'val1': 15,
            'val2': 20,
            'num_channels': 3,
            'user': self.user,
            'emails': [self.user.email]
        }
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        trigger = Trigger.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'monitor':
                self.assertEqual(payload[key], trigger.monitor.id)
            else:
                self.assertEqual(payload[key], getattr(trigger, key))

    def test_trigger_most_recent_alarm(self):
        url = reverse('measurement:trigger-list')
        payload = {
            'monitor': self.monitor.id,
            'val1': 15,
            'val2': 20,
            'num_channels': 3,
            'user': self.user,
            'emails': [self.user.email]
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        trigger = Trigger.objects.get(id=res.data['id'])

        # should have no alert
        self.assertIsNone(res.data['latest_alert'])

        # create alert with in_alarm True
        Alert.objects.create(
            trigger=trigger,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            in_alarm=True,
            user=self.user
        )
        url = reverse(
            'measurement:trigger-detail',
            kwargs={'pk': trigger.id}
        )
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # new alert with in_alarm true should make trigger have latest_alert
        self.assertIsNotNone(res2.data['latest_alert'])
        alert = Alert.objects.get(id=res2.data['latest_alert']['id'])
        self.assertEqual(
            alert.in_alarm, res2.data['latest_alert']['in_alarm'])

    def test_calc_interval_seconds_2_minutes(self):
        monitor = self.getTestMonitor(
            interval_type=Monitor.IntervalType.MINUTE,
            interval_count=2
        )
        self.assertEqual(120, monitor.calc_interval_seconds())

    def test_calc_interval_seconds_3_hours(self):
        monitor = self.getTestMonitor(interval_type=Monitor.IntervalType.HOUR,
                                      interval_count=3)
        self.assertEqual(10800, monitor.calc_interval_seconds())

    def test_calc_interval_seconds_2_days(self):
        monitor = self.getTestMonitor(interval_type=Monitor.IntervalType.DAY,
                                      interval_count=2)
        self.assertEqual(172800, monitor.calc_interval_seconds())

    def test_last_n_monitor(self):
        # Create new monitor
        group = Group.objects.get(pk=1)
        metric = Metric.objects.get(pk=1)
        monitor = Monitor.objects.create(
            channel_group=group,
            metric=metric,
            interval_type=Monitor.IntervalType.LASTN,
            interval_count=2,
            stat=Monitor.Stat.SUM,
            user=self.user
        )

        # Retrieve last n aggregate measurements
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)
        q_list = monitor.agg_measurements(endtime=endtime)

        # Calculate last n aggregate measurements separately
        chan_vals = {}
        for channel in group.channels.all():
            agg_val = sum(
                Measurement.objects.filter(
                    metric=metric,
                    channel=channel,
                    starttime__lt=endtime
                ).order_by('-starttime')[:2].values_list('value', flat=True))
            chan_vals[channel.id] = agg_val

        # Compare results
        for q_item in q_list:
            self.assertEqual(q_item['sum'], chan_vals[q_item['channel']])

    def test_agg_measurements(self):
        monitor = Monitor.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q_list), monitor.channel_group.channels.count())

        # check measurements for each channel
        expected = {}
        expected[1] = {'count': 3, 'sum': 6}
        expected[2] = {'count': 2, 'sum': 11}
        expected[3] = {'count': 1, 'sum': 8}

        for res in q_list:
            self.assertEqual(res['count'], expected[res['channel']]['count'])
            self.assertEqual(res['sum'], expected[res['channel']]['sum'])

    def test_agg_measurements_min_max_abs(self):
        # Create fake data to test minabs, maxabs
        endtime = datetime(2020, 1, 2, 3, 0, 0, 0, tzinfo=pytz.UTC)
        vals = [-20, -1, 2, 5, 12]
        for val in vals:
            Measurement.objects.create(
                metric=self.metric,
                channel=self.chan1,
                value=val,
                starttime=endtime - relativedelta(hours=5),
                endtime=endtime - relativedelta(hours=4),
                user=self.user
            )

        q_list = self.monitor.agg_measurements(endtime=endtime)

        # This monitor had 2 channels, though only one has data
        self.assertEqual(2, len(q_list))
        for q_dict in q_list:
            if self.chan1.id == q_dict['channel']:
                self.assertEqual(1, q_dict['minabs'])
                self.assertEqual(20, q_dict['maxabs'])

    def test_agg_measurements_percentile(self):
        # Create fake data to test median, p90, p95
        endtime = datetime(2020, 1, 2, 3, 0, 0, 0, tzinfo=pytz.UTC)

        for val in range(101):
            Measurement.objects.create(
                metric=self.metric,
                channel=self.chan1,
                value=val,
                starttime=endtime - relativedelta(hours=5),
                endtime=endtime - relativedelta(hours=4),
                user=self.user
            )

        q_list = self.monitor.agg_measurements(endtime=endtime)

        # This monitor had 2 channels, though only one has data
        self.assertEqual(2, len(q_list))
        for q_dict in q_list:
            if self.chan1.id == q_dict['channel']:
                self.assertEqual(50, q_dict['median'])
                self.assertEqual(90, q_dict['p90'])
                self.assertEqual(95, q_dict['p95'])

    def test_agg_measurements_missing_channel(self):
        monitor = Monitor.objects.get(pk=2)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)

        # check number of channels returned
        # (should be 3 even tho only 2 have data)
        self.assertEqual(len(q_list), monitor.channel_group.channels.count())

        # check measurements for each channel
        expected = {}
        expected[1] = {'count': 2, 'sum': 25}
        expected[2] = {'count': 1, 'sum': 14}
        expected[3] = {'count': 0, 'sum': None}

        for res in q_list:
            self.assertEqual(res['count'], expected[res['channel']]['count'])
            self.assertEqual(res['sum'], expected[res['channel']]['sum'])

    def test_agg_measurements_out_of_time_period(self):
        monitor = Monitor.objects.get(pk=2)
        endtime = datetime(2018, 2, 1, 1, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q_list), monitor.channel_group.channels.count())

        # check measurements for each  channel
        expected = {}
        expected[1] = {'count': 0, 'sum': None}
        expected[2] = {'count': 0, 'sum': None}
        expected[3] = {'count': 0, 'sum': None}

        for res in q_list:
            self.assertEqual(res['count'], expected[res['channel']]['count'])
            self.assertEqual(res['sum'], expected[res['channel']]['sum'])

    def test_agg_measurements_empty_channel_group(self):
        monitor = Monitor.objects.get(pk=3)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q_list), monitor.channel_group.channels.count())

    def test_val2_is_none_error(self):
        with self.assertRaisesRegex(ValidationError,
                                    'val2 must be defined*'):
            Trigger.objects.create(
                monitor=self.monitor,
                val1=2,
                value_operator=Trigger.ValueOperator.WITHIN,
                num_channels=5,
                user=self.user,
                emails=[self.user.email]
            )

    def test_val2_is_less_than_val1_error(self):
        with self.assertRaisesRegex(ValidationError,
                                    'val2 must be greater*'):
            Trigger.objects.create(
                monitor=self.monitor,
                val1=2,
                val2=1,
                value_operator=Trigger.ValueOperator.WITHIN,
                num_channels=5,
                user=self.user,
                emails=[self.user.email]
            )

    def test_num_channels_is_none_error(self):
        with self.assertRaisesRegex(ValidationError,
                                    'num_channels must be defined*'):
            Trigger.objects.create(
                monitor=self.monitor,
                val1=2,
                value_operator=Trigger.ValueOperator.GREATER_THAN,
                num_channels_operator=Trigger.NumChannelsOperator.GREATER_THAN,
                user=self.user,
                emails=[self.user.email]
            )

    def check_is_breaching(self, monitor_id, trigger_id, expected):
        monitor = Monitor.objects.get(pk=monitor_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)
        trigger = Trigger.objects.get(pk=trigger_id)

        # q_list should have a result for each channel, so loop over it
        self.assertEqual(len(expected), len(q_list))
        for res in q_list:
            self.assertEqual(trigger.is_breaching(res),
                             expected[res['channel']])

    def test_is_breaching(self):
        self.check_is_breaching(1, 1, {1: True, 2: True, 3: False})
        self.check_is_breaching(1, 2, {1: True, 2: True, 3: True})
        self.check_is_breaching(1, 3, {1: False, 2: False, 3: True})
        self.check_is_breaching(1, 4, {1: True, 2: True, 3: False})

    def check_get_breaching_channels(self, monitor_id, trigger_id,
                                     expected):
        monitor = Monitor.objects.get(pk=monitor_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)
        trigger = Trigger.objects.get(pk=trigger_id)

        res = trigger.get_breaching_channels(q_list)
        self.assertEqual(len(res), len(expected))

    def test_get_breaching_channels(self):
        self.check_get_breaching_channels(1, 1, [1, 2])
        self.check_get_breaching_channels(1, 2, [1, 2, 3])
        self.check_get_breaching_channels(1, 3, [3])
        self.check_get_breaching_channels(1, 4, [1, 2])

    def check_in_alarm_state(self, monitor_id, trigger_id, expected):
        monitor = Monitor.objects.get(pk=monitor_id)
        trigger = Trigger.objects.get(pk=trigger_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)
        breaching_channels = trigger.get_breaching_channels(q_list)
        self.assertEqual(trigger.in_alarm_state(breaching_channels), expected)

    def test_in_alarm_state(self):
        monitor_id = 1
        self.check_in_alarm_state(monitor_id, 1, True)
        self.check_in_alarm_state(monitor_id, 2, True)
        self.check_in_alarm_state(monitor_id, 3, False)
        self.check_in_alarm_state(monitor_id, 4, True)
        # Now change trigger and verify reverse results
        monitor = Monitor.objects.get(pk=monitor_id)
        for trigger in monitor.triggers.all():
            trigger.num_channels_operator = (
                Trigger.NumChannelsOperator.LESS_THAN
            )
            trigger.save()

        self.check_in_alarm_state(monitor_id, 1, False)
        self.check_in_alarm_state(monitor_id, 2, False)
        self.check_in_alarm_state(monitor_id, 3, True)
        self.check_in_alarm_state(monitor_id, 4, False)

    def test_all_channels_in_alarm_state(self):
        ch1 = self.getTestChannel('CH11')
        ch2 = self.getTestChannel('CH12')
        ch3 = self.getTestChannel('CH13')
        grp = Group.objects.create(
            name='Test group 2',
            user=self.user,
            organization=self.organization,
        )
        grp.channels.set([ch1.id, ch2.id])
        monitor = Monitor.objects.create(
            channel_group=grp,
            metric=self.metric,
            interval_type=Monitor.IntervalType.DAY,
            interval_count=1,
            stat=Monitor.Stat.SUM,
            user=self.user
        )
        trigger = Trigger.objects.create(
            monitor=monitor,
            val1=10,
            value_operator=Trigger.ValueOperator.GREATER_THAN,
            num_channels_operator=Trigger.NumChannelsOperator.ALL,
            user=self.user,
            emails=[self.user.email]
        )
        breaching_channels = [
            {
                "sum": 11,
                "channel": str(ch1),
                "channel_id": ch1.id
            },
            {
                "sum": 12,
                "channel": str(ch2),
                "channel_id": ch2.id
            }
        ]

        # With all two channels in the group breaching, this should alarm
        in_alarm = trigger.in_alarm_state(breaching_channels)
        self.assertTrue(in_alarm)

        # Add a channel and verify the same breaching list results in no alarm
        grp.channels.set([ch1.id, ch2.id, ch3.id])
        in_alarm = trigger.in_alarm_state(breaching_channels)
        self.assertFalse(in_alarm)

    def test_get_latest_alert(self):
        trigger = Trigger.objects.get(pk=3)

        alert = trigger.get_latest_alert()
        self.assertEqual(4, alert.id)

    def test_get_latest_alert_none_exist(self):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.get_latest_alert()
        self.assertIsNone(alert)

    def test_trigger_with_zero_vals(self):
        trigger_test = Trigger.objects.create(
            monitor=self.monitor,
            val1=0,
            val2=None,
            value_operator=Trigger.ValueOperator.LESS_THAN,
            num_channels=5,
            user=self.user
        )

        channel_value = {}
        channel_value[trigger_test.monitor.stat] = -1
        self.assertTrue(trigger_test.is_breaching(channel_value))
        channel_value[trigger_test.monitor.stat] = 1
        self.assertFalse(trigger_test.is_breaching(channel_value))

    def check_email_list(self, email_list, flag=0):
        """
        email_list is the potential input into Trigger.email_list
        flag is the anticipated result
            0: works (valid email_list)
            1: invalid input type
            2: invalid email(s)
        """
        def create_trigger(monitor, user):
            Trigger.objects.create(
                monitor=monitor,
                val1=2,
                val2=5,
                value_operator=Trigger.ValueOperator.WITHIN,
                num_channels=5,
                user=user,
                emails=email_list
            )
        if flag == 0:
            create_trigger(self.monitor, self.user)
            return

        test_str = 'Correct'
        if flag == 1:
            test_str = 'Invalid input type'
        if flag == 2:
            test_str = 'Enter a valid email address'

        with self.assertRaisesRegex(ValidationError, test_str):
            create_trigger(self.monitor, self.user)

    def test_trigger_email_list(self):
        """
        flag is the anticipated result
            0: works (valid email_list)
            1: invalid input type
            2: invalid email(s)
        """
        self.check_email_list('user', flag=2)
        self.check_email_list(['user'], flag=2)
        self.check_email_list(['user@gmail.com'], flag=0)
        self.check_email_list(['user@gmail.com', 'user'], flag=2)
        self.check_email_list(['user@gmail.com', 'user', 'other'], flag=2)
        self.check_email_list(['user@gmail.com', 'new@uw.edu'], flag=0)
        self.check_email_list({'email': 'user@gmail.com'}, flag=1)
        self.check_email_list([], flag=0)
        self.check_email_list(None, flag=0)

    def check_trigger_email_field(self, emails, expected):
        ''' Creates trigger with given email list and compares results'''

        url = reverse('measurement:trigger-detail',
                      kwargs={'pk': self.trigger.id})
        payload = {
            'emails': emails
        }
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        trigger = Trigger.objects.get(id=self.trigger.id)

        self.assertEqual(getattr(trigger, "emails"), expected)

    def test_update_trigger_with_email_field(self):
        '''
            Email field should take in string or array of strings
            validate & store as array field
        '''

        self.check_trigger_email_field('user@pnsn.org', ['user@pnsn.org'])
        self.check_trigger_email_field('', None)
        self.check_trigger_email_field(['user@pnsn.org'], ['user@pnsn.org'])
        self.check_trigger_email_field(
            'user@pnsn.org,user2@pnsn.org',
            ['user@pnsn.org', 'user2@pnsn.org'])


class PublicMonitorApiTests(TestCase):

    def getTestChannel(self, station_code):
        return Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code=station_code,
            station_name='Test Name',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )

    def getTestMonitor(self, interval_type=Monitor.IntervalType.MINUTE,
                       interval_count=2):
        return Monitor.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=interval_type,
            interval_count=interval_count,
            stat=Monitor.Stat.SUM,
            user=self.user
        )

    def getTestMeasurement(self, metric, channel, val, delta):
        basetime = datetime(2019, 5, 5, 8, 8, 7, 0, tzinfo=pytz.UTC)
        return Measurement.objects.create(
            metric=metric,
            channel=channel,
            value=val,
            starttime=basetime + delta,
            endtime=basetime + delta,
            user=self.user
        )

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all requests
        self.client.force_authenticate(user=None)
        timezone.now()
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.chan1 = self.getTestChannel('CH1')
        self.chan2 = self.getTestChannel('CH2')
        # self.chan3 = self.getTestChannel('CH3')
        self.grp = Group.objects.create(
            name='Test group',
            user=self.user,
            organization=self.organization,
        )
        self.grp.channels.set([self.chan1.id, self.chan2.id])
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            code="someotherthing",
            default_minval=1,
            default_maxval=10.0,
            user=self.user,
            reference_url='pnsn.org'
        )
        self.monitor = Monitor.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=Monitor.IntervalType.DAY,
            interval_count=1,
            stat=Monitor.Stat.SUM,
            user=self.user
        )
        self.trigger = Trigger.objects.create(
            monitor=self.monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[self.user.email]
        )

    def test_trigger_makes_valid_token(self):
        ''' check that trigger makes a token that validates
        with only the correct email and token combination '''
        email = "test@pnsn.org"
        token = self.trigger.make_token(email)

        self.assertTrue(self.trigger.check_token(token, email))

        bad_token = "testbadtoken"
        self.assertFalse(self.trigger.check_token(bad_token, email))

        bad_email = "bademail@pnsn.org"
        self.assertFalse(self.trigger.check_token(token, bad_email))

    def test_trigger_makes_valid_url(self):
        ''' check that trigger makes a url with correct information '''
        email = "test@pnsn.org"
        trigger = Trigger.objects.create(
            monitor=self.monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[email, ]
        )
        token = trigger.make_token(email)

        url = trigger.create_unsubscribe_link(email)
        self.assertEqual(
            f'/api/measurement/triggers/{trigger.id}/unsubscribe/{token}/',
            url)

    def test_trigger_unsubscribe_endpoints(self):
        '''check that unsubscribe form works'''
        email = "test2@pnsn.org"
        email2 = "other@pnsn.org"
        self.trigger.emails = [email, email2]
        self.trigger.save()

        self.assertTrue(email in self.trigger.emails)
        self.assertTrue(email2 in self.trigger.emails)

        url = self.trigger.create_unsubscribe_link(email)
        get = self.client.get(url)
        self.assertEqual(get.status_code, status.HTTP_200_OK)

        token = self.trigger.make_token(email)

        # test if unsubscribe_all only removes given email
        post = self.client.post(url, data={
            'pk': self.trigger.pk,
            'token': token,
            'unsubscribe_all': False,
            'email': email
        })

        self.assertEqual(post.status_code, status.HTTP_200_OK)

        trigger = Trigger.objects.get(pk=self.trigger.pk)
        self.assertFalse(email in trigger.emails)
        self.assertTrue(email2 in trigger.emails)

    def test_trigger_unsubscribe_all(self):
        ''' check if trigger will remove email from all
        triggers with the same monitor '''
        email = self.user.email
        email2 = "other@pnsn.org"
        self.trigger.emails = [email, email2]
        self.trigger.save()

        monitor = self.monitor

        # trigger without emails
        Trigger.objects.create(
            monitor=monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[email, email2]
        )

        # trigger with one emails
        Trigger.objects.create(
            monitor=monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[email, email2]
        )
        # trigger with one emails
        Trigger.objects.create(
            monitor=monitor,
            val1=2,
            val2=5,
            value_operator=Trigger.ValueOperator.WITHIN,
            num_channels=5,
            user=self.user,
            emails=[email2, ]
        )

        triggers = Trigger.objects.filter(monitor=monitor)
        self.assertEqual(len(triggers), 4)

        url = self.trigger.create_unsubscribe_link(email)
        token = self.trigger.make_token(email)

        # test if unsubscribe_all only removes given email
        # from all related triggers
        post = self.client.post(url, data={
            'pk': self.trigger.pk,
            'token': token,
            'unsubscribe_all': True,
            'email': email
        })

        self.assertEqual(post.status_code, status.HTTP_200_OK)

        triggers = Trigger.objects.filter(monitor=monitor)

        # make sure email was removed and others are unaffected
        for trigger in triggers:
            self.assertFalse(email in trigger.emails)
            self.assertTrue(email2 in trigger.emails)

    def test_unauthenticated_user_trigger_requests(self):
        ''' Make sure unauthenticated/non-owner users can't
        edit the trigger outside of unsubscribe'''

        url = reverse('measurement:trigger-list')
        payload = {
            'monitor': self.monitor.id,
            'val1': 15,
            'val2': 20,
            'num_channels': 3,
            'user': self.user,
            'emails': [self.user.email]
        }
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('measurement:trigger-detail',
                      kwargs={'pk': self.trigger.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
