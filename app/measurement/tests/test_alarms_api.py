from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
# from django.db.models import Avg, Count, Max, Min, Sum

from measurement.models import (Alarm, AlarmThreshold, Alert, Measurement,
                                Metric)
from nslc.models import Channel, Group, Network
from organization.models import Organization

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime, timedelta
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
        self.chan3 = self.getTestChannel('CH3')
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
        self.metric2 = Metric.objects.create(
            name='Sample metric 2',
            unit='hectare',
            code="something",
            default_minval=15,
            default_maxval=20.0,
            user=self.user,
            reference_url='pnsn.org'
        )
        # Simulate measurements for different channels
        self.m11 = self.getTestMeasurement(self.metric, self.chan1, 1,
                                           timedelta(days=0))
        self.m12 = self.getTestMeasurement(self.metric, self.chan1, 2,
                                           timedelta(days=0.5))
        self.m13 = self.getTestMeasurement(self.metric, self.chan1, 3,
                                           timedelta(days=0.9))
        self.m14 = self.getTestMeasurement(self.metric, self.chan1, 4,
                                           timedelta(days=1.1))
        self.m15 = self.getTestMeasurement(self.metric2, self.chan1, 50,
                                           timedelta(days=0.5))
        self.m21 = self.getTestMeasurement(self.metric, self.chan2, 5,
                                           timedelta(days=0))
        self.m22 = self.getTestMeasurement(self.metric, self.chan2, 6,
                                           timedelta(days=0.5))
        self.m31 = self.getTestMeasurement(self.metric, self.chan3, 7,
                                           timedelta(days=0))
        self.m32 = self.getTestMeasurement(self.metric, self.chan3, 8,
                                           timedelta(days=0.5))
        self.alarm = Alarm.objects.create(
            channel_group=self.grp,
            metric=self.metric,
            interval_type=Alarm.DAY,
            interval_count=1,
            num_channels=5,
            stat=Alarm.SUM,
            user=self.user
        )
        self.alarm_threshold = AlarmThreshold.objects.create(
            alarm=self.alarm,
            minval=2,
            maxval=5,
            level=1,
            user=self.user
        )
        self.alert = Alert.objects.create(
            alarm_threshold=self.alarm_threshold,
            timestamp=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            message='Alarm on channel group something something!',
            in_alarm=True,
            user=self.user
        )

    def test_get_alarm(self):
        url = reverse(
            'measurement:alarm-detail',
            kwargs={'pk': self.alarm.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['interval_type'], Alarm.DAY)

    def test_create_alarm(self):
        url = reverse('measurement:alarm-list')
        payload = {
            'channel_group': self.grp.id,
            'metric': self.metric.id,
            'interval_type': Alarm.MINUTE,
            'interval_count': 5,
            'num_channels': 3,
            'stat': Alarm.SUM,
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
            'level': 2,
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

    def test_agg_measurements(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # check number of channels returned
        self.assertEqual(len(q), 3)

        # check number of measurements per channel
        self.assertEqual(q.get(channel=1)['count'], 3)
        self.assertEqual(q.get(channel=1)['sum'], 6)
        self.assertEqual(q.get(channel=2)['count'], 2)
        self.assertEqual(q.get(channel=2)['sum'], 11)
        self.assertEqual(q.get(channel=3)['count'], 1)
        self.assertEqual(q.get(channel=3)['sum'], 8)

        print(q)
        print('Done with checker')

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

    def test_is_breaching_only_minval(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)
        alarm_threshold = AlarmThreshold.objects.get(pk=1)

        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=1)))
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=2)))
        self.assertFalse(alarm_threshold.is_breaching(q.get(channel=3)))

        res = alarm_threshold.get_breaching_channels(q)
        self.assertCountEqual(res, [1, 2])
        self.assertTrue(alarm_threshold.in_alarm_state(q))

    def test_is_breaching_only_maxval(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)
        alarm_threshold = AlarmThreshold.objects.get(pk=2)

        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=1)))
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=2)))
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=3)))

        res = alarm_threshold.get_breaching_channels(q)
        self.assertCountEqual(res, [1, 2, 3])
        self.assertTrue(alarm_threshold.in_alarm_state(q))

    def test_is_breaching_band(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        q = alarm.agg_measurements(endtime=endtime)

        # Check first alarm_threshold, band_inclusive = False
        alarm_threshold = AlarmThreshold.objects.get(pk=3)
        self.assertFalse(alarm_threshold.is_breaching(q.get(channel=1)))
        self.assertFalse(alarm_threshold.is_breaching(q.get(channel=2)))
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=3)))

        res = alarm_threshold.get_breaching_channels(q)
        self.assertCountEqual(res, [3])
        self.assertFalse(alarm_threshold.in_alarm_state(q))

        # Check second alarm_threshold, band_inclusive = True
        alarm_threshold = AlarmThreshold.objects.get(pk=4)
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=1)))
        self.assertTrue(alarm_threshold.is_breaching(q.get(channel=2)))
        self.assertFalse(alarm_threshold.is_breaching(q.get(channel=3)))

        res = alarm_threshold.get_breaching_channels(q)
        self.assertCountEqual(res, [1, 2])
        self.assertTrue(alarm_threshold.in_alarm_state(q))

    def test_evaluate_alarm_breach_with_alert(self):
        alarm = Alarm.objects.get(pk=1)
        endtime = datetime(2018, 2, 1, 4, 30, 0, 0, tzinfo=pytz.UTC)

        all_alerts = Alert.objects.all()
        self.assertEqual(len(all_alerts), 4)

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
        # already had an active alert, check that in_alarm is turned to False
        alarm_threshold = AlarmThreshold.objects.get(pk=3)
        alerts = alarm_threshold.alerts.all()
        self.assertEqual(len(alerts), 1)
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
        self.assertEqual(len(all_alerts), 6)
