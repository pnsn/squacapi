from django.test import TestCase
from nslc.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from organization.models import Organization

'''Tests for custom nslc filters in views.py

    to run only the app tests:
    /mg.sh "test nslc && flake8"
    to run only this file
    ./mg.sh "test nslc.tests.test_nslc_filters  && flake8"

'''


class NslcFilterTests(TestCase):
    # Tests for nslc filters
    fixtures = ['core_user.json', 'base.json']

    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Org")
        self.user = get_user_model().objects.create_user(
            email="test@pnsn.org",
            password="secret",
            organization=self.organization)
        self.user.is_staff = True
        self.client.force_authenticate(self.user)

    def test_network_filter(self):
        url = reverse('nslc:network-list')
        url += '?network=uw,cc'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_channel_filter(self):
        url = reverse('nslc:channel-list')
        url += '?channel=hnn,hnz'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_channel_nslc_filter(self):
        url = reverse('nslc:channel-list')
        url += '?nslc=uw.reed.--.hnn,uw.reed.--.hnz'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_channel_lat_lon_filter(self):
        url_root = reverse('nslc:channel-list')
        url = url_root + \
            '?lat_min=40.0&lat_max=44.0&lon_min=-124.0&lon_max=-120.0'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 10)
        url = url_root + \
            '?lat_min=40.0&lat_max=42.0&lon_min=-124.0&lon_max=-120.0'
        res = self.client.get(url)
        self.assertEqual(len(res.data), 6)

    def test_channel_date_filter(self):
        baseurl = reverse('nslc:channel-list')
        endtime = '2018-02-01T03:00:00Z'
        url = baseurl + f'?endafter={endtime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 10)
        endtime = '2018-02-01T03:00:00Z'
        url = baseurl + f'?endbefore={endtime}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_chan_search_filter(self):
        url = reverse('nslc:channel-list')
        url += '?chan_search=..z'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        channel_count = 0
        for d in res.data:
            if d['class_name'] == 'channel':
                channel_count += 1
                self.assertEqual(d['code'][2], 'z')
        self.assertEqual(channel_count, 2)

    def test_loc_search_filter(self):
        url = reverse('nslc:channel-list')
        url += '?loc_search=-.'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        channel_count = 0
        for d in res.data:
            if d['class_name'] == 'channel':
                channel_count += 1
                self.assertEqual(d['loc'][0], '-')
        self.assertEqual(channel_count, 8)

    def test_net_search_filter(self):
        url = reverse('nslc:channel-list')
        url += '?net_search=u.'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        channel_count = 0
        for d in res.data:
            if d['class_name'] == 'channel':
                channel_count += 1
                self.assertEqual(d['network'][0], 'u')
        self.assertEqual(channel_count, 10)

    def test_sta_search_filter(self):
        url = reverse('nslc:channel-list')
        url += '?sta_search=d.'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        channel_count = 0
        for d in res.data:
            if d['class_name'] == 'channel':
                channel_count += 1
                self.assertEqual(d['station_code'][0], 'd')
        self.assertEqual(channel_count, 3)

    def test_bad_channel_request(self):
        url = reverse('nslc:channel-list')
        url += '?channel=...abc'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_widget_dashboard_filter(self):
        groups = Group.objects.all()
        for g in groups:
            url = reverse('nslc:matching-rule-list')
            url += f'?group={g.id}'
            res = self.client.get(url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            group = Group.objects.get(id=g.id)
            matching_rules = group.matching_rules.all()
            self.assertEqual(len(matching_rules), len(res.data))
