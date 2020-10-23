from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Max, Min, Sum

from measurement.models import (Alarm, AlarmThreshold, Alert, Measurement,
                                Metric)
from nslc.models import Channel, Group, Network
from organization.models import Organization

from rest_framework.test import APIClient
from rest_framework import status

from datetime import date, datetime, timedelta
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

    def test_retrieve_channels(self):
        url = reverse(
            'measurement:alarm-detail',
            kwargs={'pk': self.alarm.id}
        )
        res = self.client.get(url)
        grp_id = res.data['channel_group']
        print('grp_id = {}'.format(grp_id))
        group = Group.objects.get(pk=grp_id)
        group.refresh_from_db()
        print(group.channels.all())

        date1 = datetime(2019, 5, 5, 8, 8, 7, tzinfo=pytz.UTC)
        date2 = datetime(2019, 5, 6, 8, 8, 7, tzinfo=pytz.UTC)

        res1 = Measurement.objects.filter(starttime__date=date(2019, 5, 5))
        print('len(res1) = {}'.format(len(res1)))

        res2 = Measurement.objects.filter(starttime__range=(date1, date2))
        print('len(res2) = {}'.format(len(res2)))

        res3 = Measurement.objects.filter(starttime__range=(date1, date2),
                                          channel__in=group.channels.all()) \
                                   .values('channel') \
                                   .annotate(Sum('value'))
        print('len(res3) = {}'.format(len(res3)))
        print(res3)
        print('alarm.channel_group = {}'.format(self.alarm.channel_group))
        print('alarm.channel_group.id = {}'
              .format(self.alarm.channel_group.id))

        group = Group.objects.get(pk=self.alarm.channel_group.id)
        res4 = Measurement.objects.filter(starttime__range=(date1, date2),
                                          channel__in=group.channels.all()) \
                                   .values('channel') \
                                   .annotate(Sum('value'))
        print('len(res4) = {}'.format(len(res4)))
        print(res4)

        res5 = Measurement.objects.filter(starttime__range=(date1, date2),
                                          channel__in=group.channels.all()) \
                                   .values('channel')
        print('len(res5) = {}'.format(len(res5)))
        print(res5)

        group = Group.objects.get(pk=self.alarm.channel_group.id)
        res6 = Measurement.objects.filter(starttime__range=(date1, date2),
                                          channel__in=group.channels.all(),
                                          metric=self.alarm.metric) \
                                   .values('channel') \
                                   .annotate(Sum('value'), Avg('value'),
                                             Max('value'), Min('value'))
        print('len(res6) = {}'.format(len(res6)))
        print(res6)
        print(type(group))
        print(group)

    def test_get_agg(self):
        # val_query_set = self.alarm.get_agg_values()
        channels = Group.objects.get(pk=self.alarm.channel_group.id) \
                                .channels.all()
        print('in get_agg')
        print(channels)

        # get channel ids from query set
        chan_ids = [10, 11]
        # for query in val_query_set:
        #     chan_ids.append(query['channel'])

        print(chan_ids)

        for channel in channels:
            print(channel)
            print(channel.id)
            print(type(channel.id))
            # Is channel in the returned query set?
            # self.assertTrue(channel.id in chan_ids)

            # Does the aggregate value match what it should?

    def test_check_json(self):
        measurements = Measurement.objects.all()
        metrics = Metric.objects.all()
        channels = Channel.objects.all()
        groups = Group.objects.all()
        alarms = Alarm.objects.all()

        print('In checker')
        print('n measurements = {}'.format(len(measurements)))
        print('n metrics = {}'.format(len(metrics)))
        print('n channels = {}'.format(len(channels)))
        print('n groups = {}'.format(len(groups)))
        print('n alarms = {}'.format(len(alarms)))

        group = groups[0]
        metric = metrics[0]
        res = Measurement.objects.filter(channel__in=group.channels.all(),
                                         metric=metric) \
                                   .values('channel') \
                                   .annotate(Sum('value'), Avg('value'),
                                             Max('value'), Min('value'))
        print('len(res) = {}'.format(len(res)))
        print(res)

        alarm = alarms[0]
        T1 = datetime(2018, 2, 1, 3, 0, 0, 0, tzinfo=pytz.UTC)
        T2 = datetime(2018, 2, 1, 4, 0, 0, 0, tzinfo=pytz.UTC)
        
        q = alarm.agg_measurements(T1=T1, T2=T2)
        print(q)
        print('Done with checker')