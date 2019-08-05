from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from nslc.models import Network, Station, Location, Channel, Group,\
                        ChannelGroup

from rest_framework.test import APIClient
from rest_framework import status

'''Tests for all nscl models:
    *Network
    *Station
    *Location
    *Channel


to run only these test:
    /mg.sh "test nslc && flake8"'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class PublicNslcApiTests(TestCase):
    '''Test the nslc api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all public tests
        self.client.force_authenticate(user=None)
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.sta = Station.objects.create(
            code='RCM', name="Camp Muir", network=self.net, user=self.user)
        self.loc = Location.objects.create(
            code='--', name="--", station=self.sta, lat=45, lon=-122,
            elev=0, user=self.user)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", location=self.loc, user=self.user)
        self.grp = Group.objects.create(
            name='Test group', is_public=True, user=self.user)
        self.changrp = ChannelGroup.objects.create(
            group=self.grp, channel=self.chan, user=self.user)

    def test_network_res_and_str(self):
        '''test if str is corrected'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "University of Washington")
        self.assertEqual(str(self.net), "UW")

        url = reverse('nslc:network-list')
        payload = {'code': "UW", "name": "University of Washington"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

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

    def test_group_res_and_str(self):
        '''Test if correct group object is returned'''
        url = reverse('nslc:group-detail', kwargs={'pk': self.grp.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test group')
        self.assertEqual(str(self.grp), 'Test group')

    def test_changroup_res(self):
        '''Test if correct channel group object is returned'''
        url = reverse(
            'nslc:channelgroup-detail',
            kwargs={'pk': self.changrp.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['group'], self.grp.id)
        self.assertEqual(res.data['channel'], self.chan.id)


class PrivateNslcAPITests(TestCase):
    '''all authenticated tests go here'''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="test@pnsn.org", password="secret")
        self.client.force_authenticate(self.user)
        # print(self.user.permissions)
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.sta = Station.objects.create(
            code='RCM', name="Camp Muir", network=self.net, user=self.user)
        self.loc = Location.objects.create(
            code='--', name="--", station=self.sta, lat=45, lon=-122,
            elev=100.0, user=self.user)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", location=self.loc, user=self.user)
        self.grp = Group.objects.create(
            name='Test group', is_public=True, user=self.user)

    def test_create_network(self):
        url = reverse('nslc:network-list')
        payload = {'code': "TN", "name": "Test network"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        network = Network.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(network, key))

    def test_create_station(self):
        '''Test that a station can be created under a network'''
        url = reverse('nslc:station-list')
        payload = {
            'code': 'TS',
            'name': 'Test station',
            'network': self.net.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        station = Station.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key != 'network':
                self.assertEqual(payload[key], getattr(station, key))
            else:
                self.assertEqual(payload[key], station.network.id)

    def test_create_location(self):
        '''Test that a location can be created under a network and station'''
        url = reverse('nslc:location-list')
        payload = {
            'code': 'TL',
            'name': 'Test location',
            'lat': 47.8,
            'lon': 122.3,
            'elev': 100.0,
            'station': self.sta.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        location = Location.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key != 'station':
                self.assertEqual(payload[key], getattr(location, key))
            else:
                self.assertEqual(payload[key], location.station.id)

    def test_create_channel(self):
        '''Test that a channel can be created under a location, station,
        and network'''
        url = reverse('nslc:channel-list')
        payload = {
            'code': 'TC',
            'name': 'Test channel',
            'sample_rate': 96.5,
            'location': self.loc.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        channel = Channel.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key != 'location':
                self.assertEqual(payload[key], getattr(channel, key))
            else:
                self.assertEqual(payload[key], channel.location.id)

    def test_create_group(self):
        '''Test a group can be created'''
        url = reverse('nslc:group-list')
        payload = {
            'name': 'Test group',
            'description': 'A test',
            'is_public': True
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        group = Group.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(group, key))

    def test_create_channelgroup(self):
        '''Test a channel group can be created'''
        url = reverse('nslc:channelgroup-list')
        payload = {
            'group': self.grp.id,
            'channel': self.chan.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        changrp = ChannelGroup.objects.get(id=res.data['id'])
        self.assertEqual(payload['group'], changrp.group.id)
        self.assertEqual(payload['channel'], changrp.channel.id)
