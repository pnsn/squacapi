from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from nslc.models import Network, Station, Location, Channel

from rest_framework.test import APIClient
from rest_framework import status


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicNslcApiTests(TestCase):
    '''Test the nslc api (public)'''

    def setUp(self):
        self.client = APIClient()
        self.net1 = Network.objects.create(
            code="UW", name="University of Washington")
        self.net2 = Network.objects.create(
            code="UO", name="University of Oregon")

        self.sta1 = Station.objects.create(
            code='RCM', name="Camp Muir", network=self.net1)
        self.sta2 = Station.objects.create(
            code='FMW', name="Fremont Peak", network=self.net2)

        self.loc1 = Location.objects.create(
            code='--', name="--", station=self.sta1, lat=45, lon=-122, elev=0)
        self.loc2 = Location.objects.create(
            code='00', name="00", station=self.sta1, lat=45, lon=-122, elev=0)

        self.chan1 = Channel.objects.create(
            code='EHZ', name="EHZ", location=self.loc2)
        self.chan2 = Channel.objects.create(
            code='BHZ', name="BHZ", location=self.loc2)

    def test_networks_list_exist(self):
        url = reverse('nslc:network-list')
        '''test if network objects are returned in list'''
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_network_details_exist(self):
        '''test if correct object is returned'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "University of Washington")

    def test_station_list_exist(self):
        url = reverse('nslc:station-list')
        '''test if station objects are returned in list'''
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_station_details_exist(self):
        '''test if correct station object is returned'''
        url = reverse('nslc:station-detail', kwargs={'pk': self.sta1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Camp Muir")

    def test_location_list_exist(self):
        url = reverse('nslc:location-list')
        '''test if location objects are returned in list'''
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_location_details_exist(self):
        '''test if correct location object is returned'''
        url = reverse('nslc:location-detail', kwargs={'pk': self.loc1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "--")

    def test_channel_list_exist(self):
        '''test if channel objects are returned in list'''
        url = reverse('nslc:channel-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_channel_details_exist(self):
        '''test if correct channel object is returned'''
        url = reverse('nslc:channel-detail', kwargs={'pk': self.chan1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "EHZ")
