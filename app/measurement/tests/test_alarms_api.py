from unittest.mock import patch
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
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
import pytz
from squac.test_mixins import sample_user


'''Tests for alarms models:
to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    ./mg.sh "test measurement.tests.test_alarms_api && flake8"

'''


class PrivateAlarmAPITests(TestCase):
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
            email_list=[self.user.email]
        )
        self.alert = Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            message='Alarm on channel group something something!',
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
            'email_list': [self.user.email]
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        trigger = Trigger.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'monitor':
                self.assertEqual(payload[key], trigger.monitor.id)
            else:
                self.assertEqual(payload[key], getattr(trigger, key))

    def test_get_alert(self):
        url = reverse(
            'measurement:alert-detail',
            kwargs={'pk': self.alert.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['trigger']['id'], self.trigger.id)

    def test_create_alert(self):
        url = reverse('measurement:alert-list')
        payload = {
            'trigger': self.trigger.id,
            'timestamp': datetime(1999, 12, 31, tzinfo=pytz.UTC),
            'message': "What happened? I don't know",
            'in_alarm': False,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alert = Alert.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'trigger':
                self.assertEqual(payload[key], alert.trigger.id)
            else:
                self.assertEqual(payload[key], getattr(alert, key))

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

    def test_get_latest_alert(self):
        trigger = Trigger.objects.get(pk=3)

        alert = trigger.get_latest_alert()
        self.assertEqual(4, alert.id)

    def test_get_latest_alert_none_exist(self):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.get_latest_alert()
        self.assertIsNone(alert)

    """
    These next evaluate_alert(in_alarm) tests depend on three main inputs.
    - The previous alert can be in_alarm=false, in_alarm=true, or none
    - The in_alarm argument can be false ("no") or true ("in")
    - breaching_channels is only needed if num_channels_operator=any
    """
    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=1)

        alert = trigger.evaluate_alert(False)
        self.assertEqual(1, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=1)

        alert = trigger.evaluate_alert(True)
        self.assertNotEqual(1, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=2)

        alert = trigger.evaluate_alert(False)
        self.assertNotEqual(2, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_no_alarm2(self, send_alert):
        """
        Same as above except set alert_on_out_of_alarm to true
        """
        trigger = Trigger.objects.get(pk=2)
        trigger.alert_on_out_of_alarm = True
        trigger.save()

        alert = trigger.evaluate_alert(False)
        self.assertNotEqual(2, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=2)

        alert = trigger.evaluate_alert(True)
        self.assertEqual(2, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_no_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.evaluate_alert(False)
        self.assertIsNone(alert)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_in_alarm(self, send_alert):
        trigger = Trigger.objects.get(pk=4)

        alert = trigger.evaluate_alert(True)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=7)

        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        self.assertIsNone(alert)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_no_alert_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=7)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=8)

        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        self.assertEqual(6, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_false_alert_breaching2(self, send_alert):
        trigger = Trigger.objects.get(pk=8)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        self.assertNotEqual(6, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_not_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=9)

        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        self.assertNotEqual(7, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertFalse(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_not_breaching2(self, send_alert):
        """
        Same as above except set alert_on_out_of_alarm to true
        """
        trigger = Trigger.objects.get(pk=9)
        trigger.alert_on_out_of_alarm = True
        trigger.save()

        alert = trigger.evaluate_alert(
            False,
            breaching_channels=[]
        )
        self.assertNotEqual(7, alert.id)
        self.assertFalse(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_breaching(self, send_alert):
        trigger = Trigger.objects.get(pk=9)
        breaching_channels = [{
            "avg": 5,
            "channel": "UW:STA2:--:HNN",
            "channel_id": 2
        }]

        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        self.assertNotEqual(7, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertTrue(send_alert.called)

    @patch.object(Alert, 'send_alert')
    def test_evaluate_alert_true_alert_breaching2(self, send_alert):
        """
        Same as above except the same channel is breaching as the previous
        alert
        """
        trigger = Trigger.objects.get(pk=9)
        breaching_channels = [{
            "avg": 6,
            "channel": "UW:STA1:--:HNN",
            "channel_id": 1
        }]

        alert = trigger.evaluate_alert(
            True,
            breaching_channels=breaching_channels
        )
        self.assertEqual(7, alert.id)
        self.assertTrue(alert.in_alarm)
        self.assertFalse(send_alert.called)

    def test_evaluate_alarm(self):
        '''This is more like an integration test at the moment'''
        monitor = Monitor.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 35, 0, 0, tzinfo=pytz.UTC)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 8)

        monitor.evaluate_alarm(endtime=endtime)

        # trigger 1 is breached
        # had previous alert with in_alarm = False,
        # check that a new one is created
        trigger = Trigger.objects.get(pk=1)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 2)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 2 is breached
        # already had an active alert, check that in_alarm is still True
        trigger = Trigger.objects.get(pk=2)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 1)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 3 is not breached
        # already had an active alert, check that there is a new one with
        # in_alarm = True
        trigger = Trigger.objects.get(pk=3)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 4)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertFalse(alert.in_alarm)

        # trigger 4 is breached
        # did not have an alert, check that new one is created
        trigger = Trigger.objects.get(pk=4)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 1)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # trigger 5 is not breached
        # did not have an alert, check that there is no new one
        trigger = Trigger.objects.get(pk=5)
        alerts = trigger.alerts.all()
        self.assertEqual(len(alerts), 0)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 11)

    def test_evaluate_alarms(self):
        '''Test evaluate_alarm command'''
        n_monitors = len(Monitor.objects.all())
        with patch('measurement.models.Monitor.evaluate_alarm') as ea:
            call_command('evaluate_alarms')
            self.assertEqual(n_monitors, ea.call_count)

    def test_send_alert(self):
        self.alert.send_alert()

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(self.alert.get_email_message() in mail.outbox[0].body)
        for email in self.alert.trigger.email_list:
            self.assertTrue(email in mail.outbox[0].recipients())

    def test_evaluate_alarms_filter_metric(self):
        '''Test evaluate_alarm command'''
        n_monitors = len(Monitor.objects.all())
        n_test2_monitors = len(Monitor.objects.filter(metric__name='test2'))
        with patch('measurement.models.Monitor.evaluate_alarm') as ea:
            call_command('evaluate_alarms', '--metric=test2')
            self.assertEqual(n_test2_monitors, ea.call_count)
            self.assertTrue(n_test2_monitors < n_monitors)

    def test_alert_queryset_sorted_by_timestamp(self):
        # Add two alerts out of (reverse) timestamp order
        Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1975, 1, 1, tzinfo=pytz.UTC),
            message='This one should come second!',
            in_alarm=True,
            user=self.user
        )
        Alert.objects.create(
            trigger=self.trigger,
            timestamp=datetime(1980, 1, 1, tzinfo=pytz.UTC),
            message='This one should come first!',
            in_alarm=True,
            user=self.user
        )

        url = reverse('measurement:alert-list')
        res = self.client.get(url)

        # Verify results are reverse sorted by timestamps
        timestamps = [alert['timestamp'] for alert in res.data]
        self.assertTrue(sorted(timestamps, reverse=True) == timestamps)

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

    def test_alert_get_email_message(self):
        monitor = Monitor.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q_list = monitor.agg_measurements(endtime=endtime)
        trigger = Trigger.objects.get(pk=2)

        breaching_channels = trigger.get_breaching_channels(q_list)
        alert = Alert.objects.create(
            trigger=trigger,
            timestamp=datetime(1975, 1, 1, tzinfo=pytz.UTC),
            message='',
            in_alarm=True,
            user=trigger.user,
            breaching_channels=breaching_channels
        )
        channels_out = alert.get_printable_channels(breaching_channels)
        self.assertTrue(str(channels_out) in alert.get_email_message())

    def test_alert_filter(self):
        '''Test filtering alerts'''
        url = reverse('measurement:alert-list')

        stime, etime = '2018-02-01T03:00:00Z', '2018-02-01T04:15:00Z'
        url1 = url + f'?timestamp_gte={stime}&timestamp_lt={etime}'
        res = self.client.get(url1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 4)

        url2 = url + '?trigger=3'
        res = self.client.get(url2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

        url3 = url + '?trigger=3&in_alarm=True'
        res = self.client.get(url3)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

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
                email_list=email_list
            )
        if flag == 0:
            create_trigger(self.monitor, self.user)
            return

        test_str = 'Correct'
        if flag == 1:
            test_str = 'Invalid input type'
        if flag == 2:
            test_str = 'Invalid email address'

        with self.assertRaisesRegex(ValidationError, test_str + '*'):
            create_trigger(self.monitor, self.user)

    def test_trigger_email_list(self):
        """
        flag is the anticipated result
            0: works (valid email_list)
            1: invalid input type
            2: invalid email(s)
        """
        self.check_email_list('user', flag=2)
        self.check_email_list('user@gmail.com', flag=0)
        self.check_email_list(['user'], flag=2)
        self.check_email_list(['user@gmail.com'], flag=0)
        self.check_email_list(['user@gmail.com', 'user'], flag=2)
        self.check_email_list(['user@gmail.com', 'user', 'other'], flag=2)
        self.check_email_list(['user@gmail.com', 'new@uw.edu'], flag=0)
        self.check_email_list({'email': 'user@gmail.com'}, flag=1)

    def test_val2_is_none_error(self):
        with self.assertRaisesRegex(ValidationError,
                                    'val2 must be defined*'):
            Trigger.objects.create(
                monitor=self.monitor,
                val1=2,
                value_operator=Trigger.ValueOperator.WITHIN,
                num_channels=5,
                user=self.user,
                email_list=self.user.email
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
                email_list=self.user.email
            )
