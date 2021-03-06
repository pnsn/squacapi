from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, Measurement
from nslc.models import Network, Channel

from rest_framework.test import APIClient
from rest_framework import status

from datetime import datetime
import pytz
from squac.test_mixins import sample_user


'''Tests for all measurement models:
    *
to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    ./mg.sh "test measurement.tests.test_measurement_api && flake8"

'''


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
            code='123',
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user,
            reference_url='pnsn.org'
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
            'code': 'somefukinthing',
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
    '''For authenticated tests in measuremnt API

        Authenticate and make user admin so we are only testing
        routes and methods
    '''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.user.is_staff = True
        self.client.force_authenticate(self.user)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            code="someotherfuknthing",
            default_minval=1,
            default_maxval=10.0,
            user=self.user,
            reference_url='pnsn.org'
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
            'code': 'coolname',
            'description': 'Test description',
            'unit': 'meter',
            'default_minval': 1,
            'default_maxval': 10.0,
            'user': self.user,
            "reference_url": 'pnsn.org'
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

    def test_update_or_create_measurement(self):
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

        payload = {
            'metric': self.metric.id,
            'channel': self.chan.id,
            'value': 49.0,
            'starttime': datetime(
                2019, 4, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            'endtime': datetime(2019, 4, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            'user': self.user
        }
        res_update = self.client.post(url, payload)
        self.assertEqual(res_update.status_code, status.HTTP_201_CREATED)

        self.assertEqual(res.data['id'], res_update.data['id'])
        self.assertEqual(res_update.data['value'], 49)

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

    def test_create_multiple_measurements_with_error(self):
        ''' test a bulk upload with bad param in one object'''
        url = reverse('measurement:measurement-list')
        measurements = Measurement.objects.all()
        len_before_create = len(measurements)

        payload = [
            {
                'metric': self.metric.id,
                'channel': self.chan.id,
                'value': None,
                'starttime': datetime(
                    2019, 1, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
                'endtime': datetime(
                    2019, 1, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC)
            },
            {
                'metric': self.metric.id,
                'channel': self.chan.id,
                'value': 1.0,
                'starttime': datetime(
                    2019, 3, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
                'endtime': datetime(
                    2019, 3, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC)
            }
        ]
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        update_measurements = measurements.all()
        self.assertEqual(len_before_create, len(update_measurements))
