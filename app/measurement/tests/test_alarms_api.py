from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, Alarm, AlarmThreshold, Alert
from nslc.models import Group
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

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.user.is_staff = True
        self.client.force_authenticate(self.user)
        timezone.now()
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            share_all=True,
            share_org=True,
            user=self.user,
            organization=self.organization
        )
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
            interval_type='hour',
            interval_count=2,
            num_channels=5,
            stat='sum',
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
            alarm=self.alarm,
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
        self.assertEqual(res.data['interval_type'], 'hour')

    def test_create_alarm(self):
        url = reverse('measurement:alarm-list')
        payload = {
            'channel_group': self.grp.id,
            'metric': self.metric.id,
            'interval_type': 'minute',
            'interval_count': 5,
            'num_channels': 3,
            'stat': 'avg',
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
        self.assertEqual(res.data['alarm'], self.alarm.id)

    def test_create_alert(self):
        url = reverse('measurement:alert-list')
        payload = {
            'alarm': self.alarm.id,
            'timestamp': datetime(1999, 12, 31, tzinfo=pytz.UTC),
            'message': "What happened? I don't know",
            'in_alarm': False,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alert = Alert.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'alarm':
                self.assertEqual(payload[key], alert.alarm.id)
            else:
                self.assertEqual(payload[key], getattr(alert, key))
