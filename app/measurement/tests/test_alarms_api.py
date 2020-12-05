from unittest.mock import patch
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
# from django.db.models import Avg, Count, Max, Min, Sum

from core.models import Notification
from measurement.models import (Alarm, AlarmThreshold, Alert, Measurement,
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
    fixtures = ['fixtures_measurements.json']

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

    def getTestAlarm(self, interval_type=Alarm.IntervalType.MINUTE,
                     interval_count=2):
        return Alarm.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=interval_type,
            interval_count=interval_count,
            num_channels=5,
            stat=Alarm.Stat.SUM,
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
            share_all=True,
            share_org=True,
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
        self.alarm = Alarm.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=Alarm.IntervalType.DAY,
            interval_count=1,
            num_channels=5,
            stat=Alarm.Stat.SUM,
            user=self.user
        )
        self.alarm_threshold = AlarmThreshold.objects.create(
            alarm=self.alarm,
            minval=2,
            maxval=5,
            level=AlarmThreshold.Level.ONE,
            user=self.user
        )
        self.alert = Alert.objects.create(
            alarm_threshold=self.alarm_threshold,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            message='Alarm on channel group something something!',
            in_alarm=True,
            user=self.user
        )
        self.notification = Notification.objects.create(
            notification_type=Notification.NotificationType.EMAIL,
            user=self.user,
            value=self.user.email
        )

    def test_get_alarm(self):
        url = reverse(
            'measurement:alarm-detail',
            kwargs={'pk': self.alarm.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['interval_type'], Alarm.IntervalType.DAY)

    def test_create_alarm(self):
        url = reverse('measurement:alarm-list')
        payload = {
            'channel_group': self.grp.id,
            'metric': self.metric.id,
            'interval_type': Alarm.IntervalType.MINUTE,
            'interval_count': 5,
            'num_channels': 3,
            'stat': Alarm.Stat.SUM,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alarm = Alarm.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'channel_group':
                self.assertEqual(payload[key], alarm.channel_group.id)
            elif key == 'metric':
                self.assertEqual(payload[key], alarm.metric.id)
            else:
                self.assertEqual(payload[key], getattr(alarm, key))

    def test_get_alarm_threshold(self):
        url = reverse(
            'measurement:alarm-threshold-detail',
            kwargs={'pk': self.alarm_threshold.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['alarm'], self.alarm.id)

    def test_create_alarm_threshold(self):
        url = reverse('measurement:alarm-threshold-list')
        payload = {
            'alarm': self.alarm.id,
            'minval': 15,
            'maxval': 20,
            'level': AlarmThreshold.Level.TWO,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alarm_threshold = AlarmThreshold.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'alarm':
                self.assertEqual(payload[key], alarm_threshold.alarm.id)
            else:
                self.assertEqual(payload[key], getattr(alarm_threshold, key))

    def test_get_alert(self):
        url = reverse(
            'measurement:alert-detail',
            kwargs={'pk': self.alert.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['alarm_threshold'], self.alarm_threshold.id)

    def test_create_alert(self):
        url = reverse('measurement:alert-list')
        payload = {
            'alarm_threshold': self.alarm_threshold.id,
            'timestamp': datetime(1999, 12, 31, tzinfo=pytz.UTC),
            'message': "What happened? I don't know",
            'in_alarm': False,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alert = Alert.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'alarm_threshold':
                self.assertEqual(payload[key], alert.alarm_threshold.id)
            else:
                self.assertEqual(payload[key], getattr(alert, key))

    def test_calc_interval_seconds_2_minutes(self):
        alarm = self.getTestAlarm(interval_type=Alarm.IntervalType.MINUTE,
                                  interval_count=2)
        self.assertEqual(120, alarm.calc_interval_seconds())

    def test_calc_interval_seconds_3_hours(self):
        alarm = self.getTestAlarm(interval_type=Alarm.IntervalType.HOUR,
                                  interval_count=3)
        self.assertEqual(10800, alarm.calc_interval_seconds())

    def test_calc_interval_seconds_2_days(self):
        alarm = self.getTestAlarm(interval_type=Alarm.IntervalType.DAY,
                                  interval_count=2)
        self.assertEqual(172800, alarm.calc_interval_seconds())

    def test_agg_measurements(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q), 3)

        # check measurements for each channel
        self.assertEqual(q.get(channel=1)['count'], 3)
        self.assertEqual(q.get(channel=1)['sum'], 6)
        self.assertEqual(q.get(channel=2)['count'], 2)
        self.assertEqual(q.get(channel=2)['sum'], 11)
        self.assertEqual(q.get(channel=3)['count'], 1)
        self.assertEqual(q.get(channel=3)['sum'], 8)

    def test_agg_measurements_missing_channel(self):
        alarm = Alarm.objects.get(pk=2)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q), 2)

        # check number of measurements per channel
        self.assertEqual(q.get(channel=1)['count'], 2)
        self.assertEqual(q.get(channel=1)['sum'], 25)
        self.assertEqual(q.get(channel=2)['count'], 1)
        self.assertEqual(q.get(channel=2)['sum'], 14)

    def test_agg_measurements_out_of_time_period(self):
        alarm = Alarm.objects.get(pk=2)
        endtime = datetime(2018, 2, 1, 1, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q), 0)

    def test_agg_measurements_empty_channel_group(self):
        alarm = Alarm.objects.get(pk=3)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q), 0)

    def check_is_breaching(self, alarm_id, alarm_threshold_id, expected):
        alarm = Alarm.objects.get(pk=alarm_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)
        alarm_threshold = AlarmThreshold.objects.get(pk=alarm_threshold_id)

        chan_id = 1
        for result in expected:
            if result:
                self.assertTrue(alarm_threshold
                                .is_breaching(q.get(channel=chan_id)))
            else:
                self.assertFalse(alarm_threshold
                                 .is_breaching(q.get(channel=chan_id)))
            chan_id += 1

    def test_is_breaching(self):
        self.check_is_breaching(1, 1, [True, True, False])
        self.check_is_breaching(1, 2, [True, True, True])
        self.check_is_breaching(1, 3, [False, False, True])
        self.check_is_breaching(1, 4, [True, True, False])

    def check_get_breaching_channels(self, alarm_id, alarm_threshold_id,
                                     expected):
        alarm = Alarm.objects.get(pk=alarm_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)
        alarm_threshold = AlarmThreshold.objects.get(pk=alarm_threshold_id)

        res = alarm_threshold.get_breaching_channels(q)
        self.assertCountEqual(res, expected)

    def test_get_breaching_channels(self):
        self.check_get_breaching_channels(1, 1, [1, 2])
        self.check_get_breaching_channels(1, 2, [1, 2, 3])
        self.check_get_breaching_channels(1, 3, [3])
        self.check_get_breaching_channels(1, 4, [1, 2])

    def check_in_alarm_state(self, alarm_id, alarm_threshold_id, expected):
        alarm = Alarm.objects.get(pk=alarm_id)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)
        alarm_threshold = AlarmThreshold.objects.get(pk=alarm_threshold_id)
        if expected:
            self.assertTrue(alarm_threshold.in_alarm_state(q))
        else:
            self.assertFalse(alarm_threshold.in_alarm_state(q))

    def test_in_alarm_state(self):
        self.check_in_alarm_state(1, 1, True)
        self.check_in_alarm_state(1, 2, True)
        self.check_in_alarm_state(1, 3, False)
        self.check_in_alarm_state(1, 4, True)

    def test_get_latest_alert(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=3)

        alert = alarm_threshold.get_latest_alert()
        self.assertEqual(4, alert.id)

    def test_get_latest_alert_none_exist(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=4)

        alert = alarm_threshold.get_latest_alert()
        self.assertIsNone(alert)

    def test_evaluate_alert_false_alert_no_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=1)

        alert = alarm_threshold.evaluate_alert(False)
        self.assertEqual(1, alert.id)
        self.assertFalse(alert.in_alarm)

    def test_evaluate_alert_false_alert_in_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=1)

        alert = alarm_threshold.evaluate_alert(True)
        self.assertNotEqual(1, alert.id)
        self.assertTrue(alert.in_alarm)

    def test_evaluate_alert_true_alert_no_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=2)

        alert = alarm_threshold.evaluate_alert(False)
        self.assertNotEqual(2, alert.id)
        self.assertFalse(alert.in_alarm)

    def test_evaluate_alert_true_alert_in_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=2)

        alert = alarm_threshold.evaluate_alert(True)
        self.assertEqual(2, alert.id)
        self.assertTrue(alert.in_alarm)

    def test_evaluate_alert_no_alert_no_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=4)

        alert = alarm_threshold.evaluate_alert(False)
        self.assertIsNone(alert)

    def test_evaluate_alert_no_alert_in_alarm(self):
        alarm_threshold = AlarmThreshold.objects.get(pk=4)

        alert = alarm_threshold.evaluate_alert(True)
        self.assertTrue(alert.in_alarm)

    def test_evaluate_alarm(self):
        '''This is more like an integration test at the moment'''
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 6)

        alarm.evaluate_alarm(endtime=endtime)

        # alarm_threshold 1 is breached
        # had previous alert with in_alarm = False,
        # check that a new one is created
        alarm_threshold = AlarmThreshold.objects.get(pk=1)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 2)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # alarm_threshold 2 is breached
        # already had an active alert, check that in_alarm is still True
        alarm_threshold = AlarmThreshold.objects.get(pk=2)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 1)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # alarm_threshold 3 is not breached
        # already had an active alert, check that there is a new one with
        # in_alarm = True
        alarm_threshold = AlarmThreshold.objects.get(pk=3)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 4)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertFalse(alert.in_alarm)

        # alarm_threshold 4 is breached
        # did not have an alert, check that new one is created
        alarm_threshold = AlarmThreshold.objects.get(pk=4)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 1)
        # get most recent alert
        alert = alerts.latest('timestamp')
        self.assertTrue(alert.in_alarm)

        # alarm_threshold 5 is not breached
        # did not have an alert, check that there is no new one
        alarm_threshold = AlarmThreshold.objects.get(pk=5)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 0)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 9)

    def test_evaluate_alarms(self):
        '''Test evaluate_alarm command'''
        n_alarms = len(Alarm.objects.all())
        with patch('measurement.models.Alarm.evaluate_alarm') as ea:
            call_command('evaluate_alarms')
            self.assertEqual(n_alarms, ea.call_count)
            # print('Called {} times'.format(ea.call_count))

    @patch.object(Notification, 'create_alert_notifications')
    def test_function_create_alert(self, mock):
        '''Test create_alert'''
        in_alarm = True
        alarm_threshold = AlarmThreshold.objects.get(pk=1)
        alert = alarm_threshold.create_alert(in_alarm)

        self.assertFalse(alert.id is None)
        self.assertEqual(alert.in_alarm, in_alarm)
        self.assertEqual(alarm_threshold.user, alert.user)
        self.assertTrue(mock.called)

    @patch.object(Notification, 'send')
    def test_create_alert_notification(self, mock_send):
        with patch.object(Notification,
                          'define_alert_level',
                          return_value=[self.notification.notification_type]
                          ) as mock_method:
            Notification.create_alert_notifications(self.alert)

            self.assertTrue(mock_method.called)
            self.assertEqual(mock_method.call_args[0][0],
                             self.alert.alarm_threshold.level)

            self.assertTrue(mock_send.called)
            self.assertEqual(mock_send.call_args[0][0], self.alert)
            # Alternative version
            # mock_send.assert_called_once_with(self.alert)

    @patch.object(Notification, 'send_email')
    def test_send(self, mock_send):
        # self.notification has notification_type = EMAIL
        self.notification.send(self.alert)

        self.assertTrue(mock_send.called)
        self.assertEqual(mock_send.call_args[0][0], self.alert)

    # Do more extensive testing than this?
    def test_define_alert_level(self):
        level = AlarmThreshold.Level.ONE
        notification_types = Notification.define_alert_level(level)

        expected = [Notification.NotificationType.EMAIL]
        self.assertEqual(notification_types, expected)

    def test_send_email(self):
        self.notification.send_email(self.alert)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(self.alert.message in mail.outbox[0].body)
        self.assertTrue(self.notification.value
                        in mail.outbox[0].recipients())

    # def test_evaluate_alarms_filter_metric(self):
    #     '''Test evaluate_alarm command'''
    #     n_alarms = len(Alarm.objects.all())
    #     with patch('measurement.models.Alarm.evaluate_alarm') as ea:
    #         call_command('evaluate_alarms --metric=test2')
    #         # self.assertEqual(n_alarms, ea.call_count)
    #         print('Called {} times'.format(ea.call_count))
