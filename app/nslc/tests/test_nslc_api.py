from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Network, Station, Location, Channel

from rest_framework.test import APIClient
from rest_framework import status


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class PublicNslcApiTests(TestCase):
    '''Test the nslc api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.sta = Station.objects.create(
            code='RCM', name="Camp Muir", network=self.net, user=self.user)
        self.loc = Location.objects.create(
            code='--', name="--", station=self.sta, lat=45, lon=-122,
            elev=0, user=self.user)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", location=self.loc, user=self.user)

    def test_network_res_and_str(self):
        '''test if str is corrected'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "University of Washington")
        self.assertEqual(str(self.net), "UW")

    def test_station_res_and_str(self):
        '''test if correct station object is returned'''
        url = reverse('nslc:station-detail', kwargs={'pk': self.sta.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Camp Muir")
        self.assertEqual(str(self.sta), "RCM")

    def test_location_res_and_str(self):
        '''test if correct location object is returned'''
        url = reverse('nslc:location-detail', kwargs={'pk': self.loc.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "--")
        self.assertEqual(str(self.loc), "--")

    def test_channel_res_and_str(self):
        '''test if correct channel object is returned'''
        url = reverse('nslc:channel-detail', kwargs={'pk': self.chan.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "EHZ")
        self.assertEqual(str(self.chan), "EHZ")


class PrivateNslcAPITests(TestCase):
    '''all authenticated tests go here'''

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_user)

    def test_create_network(self):
        # payload = {'code': "UW", "name": "University of Washington"}
        # res = self.client.get()
        # self.assertEqual(res.status_code, status.HTTP_200_OK)
        pass
