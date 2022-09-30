from datetime import datetime
import os
import pytz
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from nslc.models import Network, Channel, Group, MatchingRule
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
    ./mg.sh "test nslc.tests.test_nslc_api && flake8"

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
            code='EHZ', name="EHZ", location="--", latitude=45.0,
            longitude=-122.0, station='RCM', station_name='Camp Muir',
            elevation=100.0, network=self.net, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            organization=self.organization,
            user=self.user)
        self.grp.channels.add(self.chan)

    def test_network_unauthorized(self):
        '''test if unauth user can read or write to network'''
        url = reverse('nslc:network-detail', kwargs={'pk': self.net.code})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('nslc:network-list')
        payload = {'code': "UW", "name": "University of Washington"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_channel_unauthorized(self):
        '''check that unauthenticated user can't read or write to channels'''
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
            code='EHZ', name="EHZ", location="--", network=self.net,
            station='RCM', station_name='Camp Muir',
            latitude=45, longitude=-122, elevation=100.0, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            user=self.user,
            organization=self.organization
        )
        self.matching_rule = MatchingRule.objects.create(
            network_regex='uw',
            station_regex='^r.*',
            group=self.grp,
            user=self.user,
            is_include=True
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
        '''Test if auth user can get channel'''
        url = reverse('nslc:channel-detail', kwargs={'pk': self.chan.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "EHZ")
        self.assertEqual(str(self.chan), "UW.RCM.--.EHZ")

    def test_create_channel(self):
        '''Test that a channel can be created'''

        url = reverse('nslc:channel-list')
        payload = {
            'code': 'TC',
            'name': 'Test channel',
            'station': 'RCS',
            'station_name': 'Schurman',
            'sample_rate': 96.5,
            'location': "--",
            'network': self.net.code,
            'latitude': 45.0,
            'longitude': -122.0,
            'elevation': 190.0
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        channel = Channel.objects.get(id=res.data['id'])
        self.assertEqual(channel.nslc, "UW.RCS.--.TC")
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
        self.assertEqual(4, self.grp.channels.count())

    def test_create_group(self):
        '''Test a group can be created'''
        url = reverse('nslc:group-list')
        payload = {
            'name': 'Test group',
            'description': 'A test',
            'organization': self.organization.id,
            'auto_include_channels': [self.chan.id]
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_partial_update_group(self):
        group = Group.objects.get(name='UW-All')
        payload = {
            'name': 'UW-All-partial-update',
            'auto_include_channels': [self.chan.id]
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

    def test_get_matching_rule(self):
        '''test if matching rule object is returned'''
        url = reverse(
            'nslc:matching-rule-detail',
            kwargs={'pk': self.matching_rule.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue('uw' in res.data['network_regex'])
        self.assertTrue(res.data['is_include'])

    def test_create_matching_rule(self):
        url = reverse('nslc:matching-rule-list')
        payload = {
            'network_regex': 'uo',
            'station_regex': '^a.*',
            'group': self.grp.id,
            'is_include': True
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        matching_rule = MatchingRule.objects.get(id=res.data['id'])
        for key in payload.keys():
            if 'regex' in key:
                self.assertEqual(
                    payload[key], getattr(matching_rule, key).pattern)
            elif key == 'group':
                self.assertEqual(payload[key], matching_rule.group.id)
            else:
                self.assertEqual(payload[key], getattr(matching_rule, key))

    def test_full_update_group(self):
        group = Group.objects.get(name='UW-All')
        chan_list = []
        chan_id_list = []
        for i in range(5):
            chan_list.append(
                Channel.objects.create(
                    code=f"TC{i}", name=f"TC{i}", location="--",
                    network=self.net, station='RCM', station_name='Camp Muir',
                    latitude=45, longitude=-122, elevation=100.0,
                    user=self.user
                )
            )
            chan_id_list.append(chan_list[i].id)

        payload = {
            'name': 'UW-All-full-update',
            'auto_include_channels': chan_id_list,
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
                    code=f'TC{i+5}', name=f"TC{i+5}", location="--",
                    network=self.net, latitude=45, longitude=-122,
                    elevation=100.0, station='RCM', station_name='Camp Muir',
                    user=self.user
                )
            )

        group.channels.set(new_chan_list)
        new_channels = group.channels.all()
        self.assertEqual(len(new_channels), 5)
        for channel in new_chan_list:
            self.assertIn(channel, new_channels)

    def test_load_from_fdsn(self):
        '''Test that load script will update fields that have changed'''
        # Load new station
        station_name = 'BST23'
        os.environ['LOADER_EMAIL'] = 'contributor@pnsn.org'
        call_command('load_from_fdsn', sta=station_name)

        # Get channel, modify it
        channels = Channel.objects.all()
        chan = channels.filter(station=station_name.lower(),
                               code__contains='z')
        self.assertTrue(len(chan) >= 1)
        chan = chan[0]
        original_depth = chan.depth
        chan.depth = -999
        chan.save()

        # Verify changes are saved
        chan2 = Channel.objects.get(id=chan.id)
        self.assertEqual(chan2.depth, -999)

        # Load again, verify it has been clobbered without adding additional
        # channels
        call_command('load_from_fdsn', sta=station_name)
        chan3 = Channel.objects.get(id=chan.id)
        self.assertEqual(chan3.depth, original_depth)
        self.assertEqual(len(Channel.objects.all()), len(channels))

    def test_update_channels_no_rules(self):
        '''Test that a group with no matching rules or
            auto_update channels will have no channels'''
        group = Group.objects.create(
            name='auto group',
            user=self.user,
            organization=self.organization
        )
        self.assertEqual(0, group.channels.count())
        # Now call update_channels and verify nothing changes
        group.update_channels()
        self.assertEqual(0, group.channels.count())

    def test_update_channels_include_matching(self):
        '''Test that a group will update on rule update'''
        self.assertEqual(4, self.grp.channels.count())
        MatchingRule.objects.create(
            network_regex='uo',
            channel_regex='..z',
            group=self.grp,
            user=self.user,
            is_include=True
        )
        # number of channels increases
        self.assertEqual(5, self.grp.channels.count())

    def test_update_channels_exclude_matching(self):
        '''Test that a group with excluding matching rules will auto-update'''
        MatchingRule.objects.create(
            network_regex='uw',
            channel_regex='..z',
            group=self.grp,
            user=self.user,
            is_include=False
        )
        self.grp.update_channels()
        self.assertEqual(2, self.grp.channels.count())

    def test_update_channels_include_list(self):
        '''Test that a group with an include list will auto-update'''
        chan2 = Channel.objects.create(
            code='EHE', name="EHE", location="--", latitude=45.0,
            longitude=-122.0, station='TESTY', station_name='test sta 2',
            elevation=100.0, network=self.net, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.grp.auto_include_channels.add(chan2)
        self.grp.update_channels()
        self.assertEqual(5, self.grp.channels.count())

    def test_update_channels_exclude_list(self):
        '''Test that a group with an exclude list will auto-update'''
        # Add a channel to the exclude list
        chan_exclude = Channel.objects.filter(
            station__iregex='^REED',
            code__iregex='..E'
        )
        self.grp.auto_exclude_channels.set(chan_exclude)
        # Also add some random channel that wouldn't be included in the
        # first place
        chan3 = Channel.objects.create(
            code='EHE', name="EHN", location="--", latitude=45.0,
            longitude=-122.0, station='TEST3', station_name='test sta 3',
            elevation=100.0, network=self.net, user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))

        self.grp.auto_exclude_channels.add(chan3)

        self.grp.update_channels()
        self.assertEqual(3, self.grp.channels.count())

    def test_update_auto_channels(self):
        '''Test update_auto_channels command'''
        n_groups = len(Group.objects.all())
        with patch('nslc.models.Group.update_channels') as com:
            call_command('update_auto_channels')
            self.assertEqual(n_groups, com.call_count)

    def test_update_auto_channels_filter_group(self):
        '''Test update_auto_channels command with group filter'''
        n_groups = len(Group.objects.all())
        n_groups_filter = len(Group.objects.filter(id__in=[3, 17]))
        with patch('nslc.models.Group.update_channels') as com:
            call_command('update_auto_channels', channel_groups=[3, 17])
            self.assertEqual(n_groups_filter, com.call_count)
            self.assertTrue(n_groups_filter < n_groups)
