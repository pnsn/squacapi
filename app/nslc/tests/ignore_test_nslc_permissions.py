from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as UserGroup, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime
import pytz
from nslc.models import Network, Channel, Group
from organizations.models import Organization


'''
    to run this file only
    ./mg.sh "test nslc.tests.test_nslc_permissions && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


'''permissons follow form

    view_model
    add_model
    change_model
    delete_model

   groups are the only obj_permission model
'''


def create_group(name, permissions):
    '''takes name of group and list of permissions'''
    app_label = 'nslc'
    group = UserGroup.objects.create(name=name)
    for p in permissions:
        model = p.split("_")[1]
        ct = ContentType.objects.get(app_label=app_label, model=model)
        perm = Permission.objects.get(codename=p, content_type_id=ct.id)
        group.permissions.add(perm)
    return group


REPORTER_PERMISSIONS = [
    'view_network',
    'view_channel',
    'view_group', 'add_group', 'change_group', 'delete_group']

VIEWER_PERMISSIONS = [
    'view_network',
    'view_channel',
    'view_group']


class NslcPermissionTests(TestCase):
    '''Test authenticated reporter permissions'''

    def setUp(self):
        '''create sample authenticated user'''
        # import pdb; pdb.set_trace()
        self.reporter = sample_user()
        self.viewer = sample_user('viewer@pnsn.org')
        self.other = sample_user('other@pnsn.org')
        self.reporter_client = APIClient()
        self.viewer_client = APIClient()

        self.reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.reporter.groups.add(self.reporter_group)
        self.viewer.groups.add(self.viewer_group)
        self.reporter_client.force_authenticate(user=self.reporter)
        self.viewer_client.force_authenticate(user=self.viewer)

        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.reporter)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", loc="--", network=self.net,
            station_code='RCM', station_name='Camp Muir',
            lat=45, lon=-122, elev=100.0, user=self.reporter,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        self.organization = Organization.objects.create(
            name='PNSN',
            slug='pnsn'
        )

        self.grp_public = Group.objects.create(
            name='group public',
            share_all=True,
            share_org=True,
            user=self.reporter,
            organization=self.organization
        )
        self.grp_private = Group.objects.create(
            name='group private',
            share_all=False,
            share_org=False,
            user=self.reporter,
            organization=self.organization

        )
        self.grp_other_public = Group.objects.create(
            name='other public',
            share_all=True,
            share_org=True,
            user=self.other,
            organization=self.organization

        )
        self.grp_other_private = Group.objects.create(
            name='other private',
            share_all=False,
            share_org=False,
            user=self.other,
            organization=self.organization

        )

    def test_reporter_has_perms(self):
        '''reporters can:

            *view only on network and channel
            *view/add/change/delete on group
        '''
        self.assertTrue(self.reporter.has_perm('nslc.view_network'))
        self.assertFalse(self.reporter.has_perm('nslc.add_network'))
        self.assertFalse(self.reporter.has_perm('nslc.change_network'))
        self.assertFalse(self.reporter.has_perm('nslc.delete_network'))

        self.assertTrue(self.reporter.has_perm('nslc.view_channel'))
        self.assertFalse(self.reporter.has_perm('nslc.add_channel'))
        self.assertFalse(self.reporter.has_perm('nslc.change_channel'))
        self.assertFalse(self.reporter.has_perm('nslc.delete_channel'))

        self.assertTrue(self.reporter.has_perm('nslc.view_group'))
        self.assertTrue(self.reporter.has_perm('nslc.add_group'))
        self.assertTrue(self.reporter.has_perm('nslc.change_group'))
        self.assertTrue(self.reporter.has_perm('nslc.delete_group'))

    def test_viewer_has_perms(self):
        '''reporters can view all models'''
        self.assertTrue(self.viewer.has_perm('nslc.view_network'))
        self.assertFalse(self.viewer.has_perm('nslc.add_network'))
        self.assertFalse(self.viewer.has_perm('nslc.change_network'))
        self.assertFalse(self.viewer.has_perm('nslc.delete_network'))

        self.assertTrue(self.viewer.has_perm('nslc.view_channel'))
        self.assertFalse(self.viewer.has_perm('nslc.add_channel'))
        self.assertFalse(self.viewer.has_perm('nslc.change_channel'))
        self.assertFalse(self.viewer.has_perm('nslc.delete_channel'))

        self.assertTrue(self.viewer.has_perm('nslc.view_group'))
        self.assertFalse(self.viewer.has_perm('nslc.add_group'))
        self.assertFalse(self.viewer.has_perm('nslc.change_group'))
        self.assertFalse(self.viewer.has_perm('nslc.delete_group'))

    # #### groups tests ####
    def test_reporter_viewer_view_public_group(self):
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.grp_public.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_view_group_list(self):
        url = reverse('nslc:group-list')
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(len(res.data), 2)

        res = self.reporter_client.get(url)
        self.assertEqual(len(res.data), 3)

    def test_viewer_reporter_create_group(self):
        url = reverse('nslc:group-list')
        payload = {
            'name': 'Test group',
            'description': 'A test',
            'share_all': True,
            'share_org': True,
            'organation': self.organization,
            'channels': [self.chan.id]
        }
        # viewer
        res = self.viewer_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # reporter
        res = self.reporter_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_reporter_edit_group(self):
        payload = {
            'name': 'UW-All-partial-update',
            'channels': [self.chan.id]
        }
        url = reverse('nslc:group-detail', args=[self.grp_public.id])
        # viewer
        res = self.viewer_client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # reporter
        res = self.reporter_client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.grp_public.refresh_from_db()
        self.assertEqual(self.grp_public.name, payload['name'])
        channels = self.grp_public.channels.all()
        self.assertEqual(len(channels), 1)
        self.assertIn(self.chan, channels)

    def test_reporter_cannot_edit_other_group(self):
        payload = {
            'name': 'UW-All-partial-update',
            'channels': [self.chan.id]
        }
        url = reverse('nslc:group-detail', args=[self.grp_other_public.id])
        # viewer
        res = self.reporter_client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_reporter_delete_group(self):
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.grp_public.id}
        )
        res = self.viewer_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_reporter_cannot_delete_other_group(self):
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.grp_other_public.id}
        )
        self.assertFalse(self.reporter.is_staff)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
