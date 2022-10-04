from django.test import TestCase
from django.contrib.auth.models import Group as UserGroup, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from datetime import datetime
import pytz
from nslc.models import Network, Channel, Group
from organization.models import Organization
from squac.test_mixins import sample_user
from django.urls import reverse
from rest_framework import status

'''
    to run this file only
    ./mg.sh "test nslc.tests.test_nslc_permissions && flake8"

'''


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
        self.me_viewer = sample_user('me_viewer@pnsn.org')
        self.me_reporter = sample_user('me_reporter@pnsn.org')
        self.not_me = sample_user('not_me@pnsn.org')
        self.staff_admin = sample_user('admin@pnsn.org')
        self.me_reporter_client = APIClient()
        self.me_viewer_client = APIClient()
        self.staff_admin_client = APIClient()

        self.me_reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.me_viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.me_reporter.groups.add(self.me_reporter_group)
        self.me_viewer.groups.add(self.me_viewer_group)
        self.staff_admin.groups.add(self.me_reporter_group)
        self.staff_admin.is_staff = True
        self.me_reporter_client.force_authenticate(user=self.me_reporter)
        self.me_viewer_client.force_authenticate(user=self.me_viewer)
        self.staff_admin_client.force_authenticate(user=self.staff_admin)

        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.me_reporter)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", loc="--", net=self.net,
            sta='RCM', sta_name='Camp Muir',
            lat=45, lon=-122, elev=100.0, user=self.me_reporter,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC))
        # create two orgs min and not mine
        self.my_org = Organization.objects.create(
            name='Mine'
        )

        self.not_my_org = Organization.objects.create(
            name='Not Mine'
        )
        # add users to orgs
        self.me_reporter.organization = self.my_org
        self.me_viewer.organization = self.my_org
        self.staff_admin.organization = self.my_org

        self.my_org_group_share_org = Group.objects.create(
            name='Test group',
            share_all=False,
            share_org=True,
            user=self.me_reporter,
            organization=self.my_org,
        )

        self.my_org_group_share_none = Group.objects.create(
            name='Test group',
            share_all=False,
            share_org=False,
            user=self.me_reporter,
            organization=self.my_org,
        )

        self.not_my_org_group_share_all = Group.objects.create(
            name='Test group',
            share_all=True,
            share_org=True,
            user=self.not_me,
            organization=self.not_my_org,
        )

        self.not_my_org_group_share_org = Group.objects.create(
            name='Test group',
            share_all=False,
            share_org=True,
            user=self.not_me,
            organization=self.not_my_org,
        )
        self.not_my_org_group_share_none = Group.objects.create(
            name='Test group',
            share_all=False,
            share_org=False,
            user=self.not_me,
            organization=self.not_my_org,
        )

    def test_reporter_has_perms(self):
        '''reporters can:

            *view only on network and channel
            *view/add/change/delete on group
        '''
        self.assertTrue(self.me_reporter.has_perm('nslc.view_network'))
        self.assertFalse(self.me_reporter.has_perm('nslc.add_network'))
        self.assertFalse(self.me_reporter.has_perm('nslc.change_network'))
        self.assertFalse(self.me_reporter.has_perm('nslc.delete_network'))

        self.assertTrue(self.me_reporter.has_perm('nslc.view_channel'))
        self.assertFalse(self.me_reporter.has_perm('nslc.add_channel'))
        self.assertFalse(self.me_reporter.has_perm('nslc.change_channel'))
        self.assertFalse(self.me_reporter.has_perm('nslc.delete_channel'))

        self.assertTrue(self.me_reporter.has_perm('nslc.view_group'))
        self.assertTrue(self.me_reporter.has_perm('nslc.add_group'))
        self.assertTrue(self.me_reporter.has_perm('nslc.change_group'))
        self.assertTrue(self.me_reporter.has_perm('nslc.delete_group'))

    def test_viewer_has_perms(self):
        '''reporters can view all models'''
        self.assertTrue(self.me_viewer.has_perm('nslc.view_network'))
        self.assertFalse(self.me_viewer.has_perm('nslc.add_network'))
        self.assertFalse(self.me_viewer.has_perm('nslc.change_network'))
        self.assertFalse(self.me_viewer.has_perm('nslc.delete_network'))

        self.assertTrue(self.me_viewer.has_perm('nslc.view_channel'))
        self.assertFalse(self.me_viewer.has_perm('nslc.add_channel'))
        self.assertFalse(self.me_viewer.has_perm('nslc.change_channel'))
        self.assertFalse(self.me_viewer.has_perm('nslc.delete_channel'))

        self.assertTrue(self.me_viewer.has_perm('nslc.view_group'))
        self.assertFalse(self.me_viewer.has_perm('nslc.add_group'))
        self.assertFalse(self.me_viewer.has_perm('nslc.change_group'))
        self.assertFalse(self.me_viewer.has_perm('nslc.delete_group'))

    def test_staff_can_view_all(self):
        '''admin should be able to view all groups'''
        url = reverse(
            'nslc:group-list'
        )
        res = self.staff_admin_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)

    # # #### groups tests ####

    def test_viewer_can_view_my_org_share_org(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.my_org_group_share_org.id}
        )
        # viewer
        res = self.me_viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_view_my_org_share_none(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.my_org_group_share_none.id}
        )
        # viewer
        res = self.me_viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_can_view_not_my_org_share_all(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.not_my_org_group_share_all.id}
        )
        # viewer
        res = self.me_viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_view_not_my_org_share_org(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.not_my_org_group_share_org.id}
        )
        # viewer
        res = self.me_viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_view_not_my_org_share_none(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'nslc:group-detail',
            kwargs={'pk': self.not_my_org_group_share_none.id}
        )
        # viewer
        res = self.me_viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
