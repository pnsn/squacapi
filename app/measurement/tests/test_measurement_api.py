from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from measurement.models import DataSource, Metric

from rest_framework.test import APIClient
from rest_framework import status

'''Tests for all measurement models:
    *

to run only these tests:
    ./mg.sh "test measurement && flake8"
'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class PublicMeasurementApiTests(TestCase):
    '''Test the measurement api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all public tests
        self.client.force_authenticate(user=None)
        self.datasrc = DataSource.objects.create(
            name='Data source test', user=self.user)
        self.metric = Metric.objects.create(
            name='Metric test',
            unit='meter',
            datasource=self.datasrc,
            user=self.user
        )

    def test_datasource_res_and_str(self):
        url = reverse(
            'measurement:datasource-detail',
            kwargs={'pk': self.datasrc.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Data source test")
        self.assertEqual(str(self.datasrc), "Data source test")

    def test_datasource_post_unauth(self):
        url = reverse('measurement:datasource-list')
        payload = {'name': 'Test'}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_metric_res_and_str(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Metric test')
        self.assertEqual(str(self.metric), 'Metric test')

    def test_metric_post_unauth(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Test',
            'unit': 'meter',
            'datasource': self.datasrc
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    '''For authenticated tests in measuremnt API'''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_create_datasource(self):
        url = reverse('measurement:datasource-list')
        payload = {'name': 'Data source test', 'user': self.user}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], payload['name'])

    def test_create_metric(self):
        url = reverse('measurement:metric-list')
        datasrc = DataSource.objects.create(name='Test', user=self.user)
        datasrc.save()
        payload = {
            'name': 'Metric test',
            'description': 'Test description',
            'unit': 'meter',
            'datasource': datasrc.id,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
