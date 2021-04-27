from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from nslc.models import Group, Channel
from organization.models import Organization


'''Tests for custom measurement filters in views.py

to run only measurement tests:
    ./mg.sh "test measurement && flake8"
to run only this file
    ./mg.sh "test measurement.tests.test_measurement_filter && flake8"

'''


class AuthenticatedMeasurementFilterTests(TestCase):
    # Public tests for filters
    fixtures = ['core_user.json', 'base.json', 'measurements.json']
    # Fixtures load from fixture directory within measurement app

    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name='PNSN')
        self.user = get_user_model().objects.create_user(
            "test@pnsn.org", "secret", organization=self.organization)
        self.user.is_staff = True
        self.client.force_authenticate(self.user)

        self.grp = Group.objects.create(
            name='Test group',
            share_all=True,
            organization=self.organization,
            user=self.user
        )
        for i in range(4, 7):
            chan = Channel.objects.get(pk=i)
            self.grp.channels.add(chan)

    def test_measurement_invalid_filter_input(self):
        # Not inputing metric, channel, starttime, and endtime should result
        # in no measurements being returned, required for proper filtering
        url = reverse('measurement:measurement-list')
        url += '?metric=284&channel=4430'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_measurement_null_values(self):
        # if any channels or metrics are not found, should still return values
        # available.
        url = reverse('measurement:measurement-list')
        stime, etime = '2020-02-01T05:00:00Z', '2020-02-02T05:00:00Z'
        url += f'?metric=3,420&channel=5,420&starttime={stime}&endtime={etime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_measurement_filter(self):
        # Test that filter properly finds the measurement that fits params
        url = reverse('measurement:measurement-list')
        stime, etime = '2016-02-01T03:00:00Z', '2020-02-02T05:00:00Z'
        url += f'?metric=3&channel=5&starttime={stime}&endtime={etime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_measurement_filter_with_group(self):
        '''test using group param'''
        url = reverse('measurement:measurement-list')
        stime, etime = '2016-02-01T03:00:00Z', '2020-02-02T05:00:00Z'
        url += f'?metric=3&channel=4,5,6&starttime={stime}&endtime={etime}'
        res1 = self.client.get(url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # now with group id
        url = reverse('measurement:measurement-list')
        url += f'?metric=3&group={self.grp.id}'\
               f'&starttime={stime}&endtime={etime}'
        res2 = self.client.get(url)

        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data, res1.data)

    def test_measurement_out_of_range_filter(self):
        # Test that filter does not return measurements outside date range
        url = reverse('measurement:measurement-list')
        stime, etime = '2020-02-01T05:00:00Z', '2020-02-02T05:00:00Z'
        url += f'?metric=3&channel=5&starttime={stime}&endtime={etime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_metric_filter(self):
        m1, m2 = 'pctavailable', 'ngaps'
        url = reverse('measurement:metric-list')
        url += f'?name={m1},{m2}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_aggregated_filter_with_group(self):
        '''test using group param'''
        url = reverse('measurement:aggregated-list')
        stime, etime = '2016-02-01T03:00:00Z', '2020-02-02T05:00:00Z'
        url += f'?metric=3,4,5&channel=4,5,6&starttime={stime}&endtime={etime}'
        res1 = self.client.get(url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # now with group id
        url = reverse('measurement:aggregated-list')
        url += f'?metric=3,4,5&group={self.grp.id}'\
               f'&starttime={stime}&endtime={etime}'
        res2 = self.client.get(url)

        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data, res1.data)
