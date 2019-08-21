from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

'''Tests for custom nslc filters in views.py'''


class PublicNslcFilterTests(TestCase):
    # Public tests for nslc filters
    fixtures = ['nslc_tests.json']
    # Fixtures load from the fixtures directory within /nslc
    # to dump data to an nslc folder run:
    # ./mg.sh "dumpdata --indent=2 >> somefolder/file.json"

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=None)

    def test_network_filter(self):
        url = reverse('nslc:network-list')
        url += '?network=uw'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for dict in res.data:
            if dict['class_name'] == 'network':
                self.assertEqual(dict['code'], 'uw')

    def test_station_filter(self):
        url = reverse('nslc:station-list')
        url += '?station=kvcs'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for dict in res.data:
            if dict['class_name'] == 'station':
                self.assertEqual(dict['code'], 'kvcs')

    def test_channel_filter(self):
        url = reverse('nslc:channel-list')
        url += '?channel=hnn'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for dict in res.data:
            if dict['class_name'] == 'channel':
                self.assertEqual(dict['code'], 'hnn')

    def test_channel_wildcard_filter(self):
        url = reverse('nslc:channel-list')
        url += '?channel=**z'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        channel_count = 0
        for dict in res.data:
            if dict['class_name'] == 'channel':
                channel_count += 1
                self.assertEqual(dict['code'][2], 'z')
        self.assertEqual(channel_count, 4)

    def test_bad_channel_request(self):
        url = reverse('nslc:channel-list')
        url += '?channel=***abc'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)
