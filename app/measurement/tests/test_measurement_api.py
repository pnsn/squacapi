from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from measurement.models import DataSource

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
        name='Test', user=self.user)

    def test_datasource_res_and_str(self):
        url = reverse(
            'measurement:datasource-detail',
            kwargs={'pk': self.datasrc.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Test")
        self.assertEqual(str(self.datasrc), "Test")
