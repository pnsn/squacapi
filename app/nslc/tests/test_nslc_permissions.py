from django.test import TestCase
from django.contrib.auth.models import Group as UserGroup, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from datetime import datetime
import pytz
from nslc.models import Network, Channel
from organization.models import Organization
from squac.test_mixins import sample_user


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
        self.me_reporter_client = APIClient()
        self.me_viewer_client = APIClient()

        self.me_reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.me_viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.me_reporter.groups.add(self.me_reporter_group)
        self.me_viewer.groups.add(self.me_viewer_group)
        self.me_reporter_client.force_authenticate(user=self.me_reporter)
        self.me_viewer_client.force_authenticate(user=self.me_viewer)

        self.net = Network.objects.create(
            code="UW", name="University of Washington", user=self.me_reporter)
        self.chan = Channel.objects.create(
            code='EHZ', name="EHZ", loc="--", network=self.net,
            station_code='RCM', station_name='Camp Muir',
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

    # # #### groups tests ####
