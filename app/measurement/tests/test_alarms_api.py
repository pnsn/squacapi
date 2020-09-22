from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, Alarms, AlarmMetric
from nslc.models import Group
from organization.models import Organization

from rest_framework.test import APIClient
from rest_framework import status

from squac.test_mixins import sample_user


'''Tests for alarms models:
to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    ./mg.sh "test measurement.tests.test_alarms_api && flake8"

'''


class PrivateAlarmsAPITests(TestCase):
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
        self.alarm = Alarms.objects.create(
            channel_group=self.grp,
            interval_type='hour',
            interval_count=2,
            user=self.user
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
        self.alarm_metric = AlarmMetric.objects.create(
            alarm=self.alarm,
            metric=self.metric,
            minval=2,
            maxval=5,
            stat='sum',
            weight=1,
            user=self.user
        )

    def test_get_alarm(self):
        url = reverse(
            'measurement:alarms-detail',
            kwargs={'pk': self.alarm.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['interval_type'], 'hour')

    def test_create_alarm(self):
        url = reverse('measurement:alarms-list')
        payload = {
            'channel_group': self.grp.id,
            'interval_type': 'minute',
            'interval_count': 5,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alarm = Alarms.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'channel_group':
                self.assertEqual(payload[key], alarm.channel_group.id)
            else:
                self.assertEqual(payload[key], getattr(alarm, key))

    def test_get_alarm_metric(self):
        url = reverse(
            'measurement:alarm-metric-detail',
            kwargs={'pk': self.alarm_metric.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['alarm'], self.alarm.id)

    def test_create_alarm_metric(self):
        url = reverse('measurement:alarm-metric-list')
        payload = {
            'alarm': self.alarm.id,
            'metric': self.metric.id,
            'minval': 15,
            'maxval': 20,
            'stat': 'avg',
            'weight': 1. / 2,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alarm_metric = AlarmMetric.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'alarm':
                self.assertEqual(payload[key], alarm_metric.alarm.id)
            elif key == 'metric':
                self.assertEqual(payload[key], alarm_metric.metric.id)
            else:
                self.assertEqual(payload[key], getattr(alarm_metric, key))
