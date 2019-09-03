from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model


'''Tests for custom measurement filters in views.py'''


class PublicMeasurementFilterTests(TestCase):
    # Public tests for filters
    fixtures = ['fixtures_all.json']
    # Fixtures load from fixture directory within measurement app

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@pnsn.org", "secret")
        self.client.force_authenticate(self.user)

    def test_measurement_invalid_filter_input(self):
        # Not inputing metric, channel, starttime, and endtime should result
        # in no measurements being returned, required for proper filtering
        url = reverse('measurement:measurement-list')
        url += '?metric=284&channel=4430'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_measurement_filter(self):
        # Test that filter properly finds the measurement that fits params
        url = reverse('measurement:measurement-list')
        stime, etime = '2018-02-01T03:00:00Z', '2018-02-02T05:00:00Z'
        url += f'?metric=2&channel=5&starttime={stime}&endtime={etime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], 1)

    def test_measurement_out_of_range_filter(self):
        # Test that filter does not return measurements outside date range
        url = reverse('measurement:measurement-list')
        stime, etime = '2018-02-01T05:00:00Z', '2018-02-02T05:00:00Z'
        url += f'?metric=284&channel=4430&starttime={stime}&endtime={etime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)
