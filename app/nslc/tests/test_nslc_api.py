from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime
import pytz
from nslc.models import Network, Channel, Group
from organization.models import Organization
from squac.test_mixins import sample_user


'''Tests for all nscl models:
    *Network
    *Channel
    *Group
    *ChannelGroup


to run only the app tests:
    /mg.sh "test nslc && flake8"
to run only this file
    ./mg.sh "test nslc.tests.test_nslc_api  && flake8"

'''


class UnAuthenticatedNslcApiTests(TestCase):
    '''Test the nslc api (public). should 401 on all requests'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate user
        self.client.force_authenticate(user=None)
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", loc="--", lat=45.0, lon=-122.0,
            station_code='RCM', station_name='Camp Muir',
            elev=100.0, network=self.net, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            share_all=True,
            share_org=True,
            organization=self.organization,
            user=self.user)
        self.grp.channels.add(self.chan)

    def test_network_unathorized(self):
        '''test if unauth user can read or write to network'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net.code})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('nslc:network-list')
        payload = {'code': "UW", "name": "University of Washington"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_channel_unauthorized(self):
        '''check that unathenticated user can't read or write to channels'''
        url = reverse('nslc:channel-detail', kwargs={'pk': self.chan.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_group_unauthorized(self):
        '''Test if unauth user can read/write groups'''
        url = reverse('nslc:group-detail', kwargs={'pk': self.grp.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateNslcAPITests(TestCase):
    '''all authenticated tests go here'''

    fixtures = ['core_user.json', 'base.json']
    # Fixtures load from the fixtures directory in app
    # Fixture for testing patch/put on group

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="test@pnsn.org", password="secret")
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.user)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", loc="--", network=self.net,
            station_code='RCM', station_name='Camp Muir',
            lat=45, lon=-122, elev=100.0, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            share_all=True,
            share_org=True,
            user=self.user,
            organization=self.organization
        )

    def test_get_network(self):
        '''test if str is corrected'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net.code})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "University of Washington")
        self.assertEqual(str(self.net), "UW")

    def test_create_network(self):
        url = reverse('nslc:network-list')
        payload = {'code': "TN", "name": "Test network"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        network = Network.objects.get(code=res.data['code'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(network, key))

    def test_get_channel(self):
        '''Test if auth user cat get channel'''
        url = reverse('nslc:channel-detail', kwargs={'pk': self.chan.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "EHZ")
        self.assertEqual(str(self.chan), "UW:RCM:--:EHZ")

    def test_create_channel(self):

        '''Test that a channel can be created'''

        url = reverse('nslc:channel-list')
        payload = {
            'code': 'TC',
            'name': 'Test channel',
            'station_code': 'RCS',
            'station_name': 'Schurman',
            'sample_rate': 96.5,
            'loc': "--",
            'network': self.net.code,
            'lat': 45.0,
            'lon': -122.0,
            'elev': 190.0
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        channel = Channel.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key != 'network':
                self.assertEqual(payload[key], getattr(channel, key))
            else:
                self.assertEqual(payload[key], channel.network.code)

    def test_get_group(self):
        '''Test if correct group object is returned'''
        url = reverse('nslc:group-detail', kwargs={'pk': self.grp.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test group')
        self.assertEqual(str(self.grp), 'Test group')
        for channel in res.data['channels']:
            self.assertEqual(channel['id'], self.chan.id)
            self.assertEqual(channel['code'], self.chan.code)

    def test_create_group(self):
        '''Test a group can be created'''
        url = reverse('nslc:group-list')
        payload = {
            'name': 'Test group',
            'description': 'A test',
            'share_all': True,
            'share_org': True,
            'organization': self.organization.id,
            'channels': [self.chan.id]
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # self.assertTrue(self.user.has_perm('nslc.change_group'))
        group = Group.objects.get(name='UW-All')
        payload = {
            'name': 'UW-All-partial-update',
            'channels': [self.chan.id],
            'share_all': True
        }
        self.assertTrue(self.user.is_staff)
        url = reverse('nslc:group-detail', args=[group.id])
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.name, payload['name'])
        self.assertEqual(group.description, "All UW channels")
        channels = group.channels.all()
        self.assertEqual(len(channels), 1)
        self.assertIn(self.chan, channels)

    def test_full_update_group(self):
        group = Group.objects.get(name='UW-All')
        chan_list = []
        chan_id_list = []
        for i in range(5):
            chan_list.append(
                Channel.objects.create(
                    code=f"TC{i}", name=f"TC{i}", loc="--", network=self.net,
                    station_code='RCM', station_name='Camp Muir',
                    lat=45, lon=-122, elev=100.0, user=self.user
                )
            )
            chan_id_list.append(chan_list[i].id)

        payload = {
            'name': 'UW-All-full-update',
            'channels': chan_id_list,
            'organization': self.organization.id
        }
        url = reverse('nslc:group-detail', args=[group.id])
        self.client.put(url, payload)
        group.refresh_from_db()
        self.assertEqual(group.name, payload['name'])
        channels = group.channels.all()
        self.assertEqual(len(channels), 5)
        for channel in chan_list:
            self.assertIn(channel, channels)

        new_chan_list = []
        for i in range(5):
            new_chan_list.append(
                Channel.objects.create(
                    code=f'TC{i+5}', name=f"TC{i+5}", loc="--",
                    network=self.net, lat=45, lon=-122, elev=100.0,
                    station_code='RCM', station_name='Camp Muir',
                    user=self.user
                )
            )

        group.channels.set(new_chan_list)
        new_channels = group.channels.all()
        self.assertEqual(len(new_channels), 5)
        for channel in new_chan_list:
            self.assertIn(channel, new_channels)
