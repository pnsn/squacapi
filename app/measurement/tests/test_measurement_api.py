from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, Measurement
from nslc.models import Network, Channel

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime
import pytz

'''Tests for all measurement models:
    *

to run only these tests:
    ./mg.sh "test measurement && flake8"
'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class UnauthenticatedMeasurementApiTests(TestCase):
    '''Test the measurement api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all requests
        self.client.force_authenticate(user=None)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Metric test',
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.measurement = Measurement.objects.create(
            metric=self.metric,
            channel=self.chan,
            value=3.0,
            starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 5, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            user=self.user
        )

    def test_unauthenticated_metric(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_metric_post_unauth(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Test',
            'unit': 'meter'
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_measurement_res_and_str(self):
        url = reverse(
            'measurement:measurement-detail',
            kwargs={'pk': self.measurement.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    '''For authenticated tests in measuremnt API'''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)

        )

        self.measurement = Measurement.objects.create(
            metric=self.metric,
            channel=self.chan,
            value=3.0,
            starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 5, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            user=self.user
        )

    def test_get_metric(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Sample metric')
        self.assertEqual(str(self.metric), 'Sample metric')

    def test_create_metric(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Metric test',
            'description': 'Test description',
            'unit': 'meter',
            'default_minval': 1,
            'default_maxval': 10.0,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        metric = Metric.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(metric, key))

    def test_get_measurement(self):
        url = reverse(
            'measurement:measurement-detail',
            kwargs={'pk': self.measurement.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['metric'], self.metric.id)
        self.assertEqual(res.data['channel'], self.chan.id)
        self.assertEqual(
            str(self.measurement),
            'Metric: Sample metric Channel: UW:RCM:--:EHZ'
        )

    def test_create_measurement(self):
        url = reverse('measurement:measurement-list')
        payload = {
            'metric': self.metric.id,
            'channel': self.chan.id,
            'value': 47.0,
            'starttime': datetime(
                2019, 4, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            'endtime': datetime(2019, 4, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        measurement = Measurement.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'metric':
                self.assertEqual(payload[key], measurement.metric.id)
            elif key == 'channel':
                self.assertEqual(payload[key], measurement.channel.id)
            else:
                self.assertEqual(payload[key], getattr(measurement, key))

    def test_create_multiple_measurements(self):
        url = reverse('measurement:measurement-list')
        measurements = Measurement.objects.all()
        len_before_create = len(measurements)

        payload = [
            {
                'metric': self.metric.id,
                'channel': self.chan.id,
                'value': 47.0,
                'starttime': datetime(
                    2019, 1, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
                'endtime': datetime(
                    2019, 1, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC)
            },
            {
                'metric': self.metric.id,
                'channel': self.chan.id,
                'value': 10.0,
                'starttime': datetime(
                    2019, 3, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
                'endtime': datetime(
                    2019, 3, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC)
            }
        ]
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        update_measurements = measurements.all()
        self.assertEqual(len_before_create + 2, len(update_measurements))
