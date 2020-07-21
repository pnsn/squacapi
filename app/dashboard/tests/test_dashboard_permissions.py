from django.test import TestCase
from organization.models import Organization
from django.contrib.auth.models import Group as UserGroup, Permission
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime
import pytz
from dashboard.models import Dashboard, Widget, WidgetType, StatType
from measurement.models import Metric
from nslc.models import Network, Channel, Group
from squac.test_mixins import sample_user

'''
    to run this file only
    ./mg.sh "test dashboard.tests.test_dashboard_permissions && flake8"

'''


'''permissons follow form

    view_model
    add_model
    change_model
    delete_model

    Widget types and stattypes use modelpermissions only so no need to test
    beyond has_perm
'''


def create_group(name, permissions):
    '''takes name of group and list of permissions'''
    group = UserGroup.objects.create(name=name)
    for p in permissions:
        perm = Permission.objects.get(codename=p)
        group.permissions.add(perm)
    return group


REPORTER_PERMISSIONS = [
    'view_dashboard', 'add_dashboard', 'change_dashboard', 'delete_dashboard',
    'view_widget', 'add_widget', 'change_widget', 'delete_widget',
    'view_widgettype',
    'view_stattype']

VIEWER_PERMISSIONS = [
    'view_dashboard',
    'view_widget',
    'view_widgettype',
    'view_stattype']


class DashboardPermissionTests(TestCase):
    '''Test authenticated reporter permissions'''

    def setUp(self):
        '''create sample authenticated user'''
        pass
        self.viewer = sample_user('viewer@pnsn.org')
        self.reporter = sample_user('reporter@pnsn.org')
        self.not_me = sample_user('not_me@pnsn.org')
        self.reporter_client = APIClient()
        self.viewer_client = APIClient()

        self.reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.reporter.groups.add(self.reporter_group)
        self.viewer.groups.add(self.viewer_group)
        self.reporter_client.force_authenticate(user=self.reporter)
        self.viewer_client.force_authenticate(user=self.viewer)

        self.metric = Metric.objects.create(
            name='Metric test',
            code="code12",
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.reporter
        )
        self.metric_other = Metric.objects.create(
            name='Metric test',
            code="code123",
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.not_me
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.reporter
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.reporter,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )

        self.my_org = Organization.objects.create(
            name='mu org'
        )
        self.not_my_org = Organization.objects.create(
            name='not my org'
        )
        # we're not tesing chan group so mark share all
        self.grp = Group.objects.create(
            name='Test group',
            share_all=True,
            share_org=True,
            user=self.reporter,
            organization=self.my_org
        )
        self.grp.channels.add(self.chan)

        self.reporter.organization = self.my_org
        self.viewer.organization = self.my_org

        self.my_org_dashboard_share_org = Dashboard.objects.create(
            name='Test dashboard',
            share_all=False,
            share_org=True,
            user=self.reporter,
            organization=self.my_org
        )

        self.my_org_dashboard_share_none = Dashboard.objects.create(
            name='Test dashboard',
            share_all=False,
            share_org=False,
            user=self.reporter,
            organization=self.my_org
        )

        self.not_my_org_dashboard_share_all = Dashboard.objects.create(
            name='Test dashboard',
            share_all=True,
            share_org=True,
            user=self.not_me,
            organization=self.not_my_org
        )

        self.not_my_org_dashboard_share_org = Dashboard.objects.create(
            name='Test dashboard',
            share_all=False,
            share_org=True,
            user=self.not_me,
            organization=self.not_my_org
        )
        self.not_my_org_dashboard_share_none = Dashboard.objects.create(
            name='Test dashboard',
            share_all=False,
            share_org=False,
            user=self.not_me,
            organization=self.not_my_org
        )

        self.widtype = WidgetType.objects.create(
            name='Test widget type',
            type='Some type',
            user=self.reporter
        )
        self.stattype = StatType.objects.create(
            name="Average",
            type="ave",
            user=self.reporter
        )
        self.widget = Widget.objects.create(
            name='Test widget',
            dashboard=self.my_org_dashboard_share_org,
            widgettype=self.widtype,
            stattype=self.stattype,
            columns=6,
            rows=3,
            x_position=1,
            y_position=1,
            user=self.reporter,
            channel_group=self.grp,
        )

    def test_reporter_has_perms(self):
        '''reporters can:

            *all actions on metrics
            *view/add on measurements and archives
        '''
        self.assertTrue(self.reporter.has_perm('dashboard.view_dashboard'))
        self.assertTrue(self.reporter.has_perm('dashboard.add_dashboard'))
        self.assertTrue(self.reporter.has_perm('dashboard.change_dashboard'))
        self.assertTrue(self.reporter.has_perm('dashboard.delete_dashboard'))

        self.assertTrue(self.reporter.has_perm('dashboard.view_widget'))
        self.assertTrue(self.reporter.has_perm('dashboard.add_widget'))
        self.assertTrue(self.reporter.has_perm('dashboard.change_widget'))
        self.assertTrue(self.reporter.has_perm('dashboard.delete_widget'))

        self.assertTrue(self.reporter.has_perm('dashboard.view_widgettype'))
        self.assertFalse(self.reporter.has_perm('dashboard.add_widgettype'))
        self.assertFalse(self.reporter.has_perm('dashboard.change_widgettype'))
        self.assertFalse(self.reporter.has_perm('dashboard.delete_widgetype'))

        self.assertTrue(self.reporter.has_perm('dashboard.view_stattype'))
        self.assertFalse(self.reporter.has_perm('dashboard.add_stattype'))
        self.assertFalse(self.reporter.has_perm('dashboard.change_stattype'))
        self.assertFalse(self.reporter.has_perm('dashboard.delete_stattype'))

    def test_viewer_has_perms(self):
        '''viewers can view all models'''
        self.assertTrue(self.viewer.has_perm('dashboard.view_dashboard'))
        self.assertFalse(self.viewer.has_perm('dashboard.add_dashboard'))
        self.assertFalse(self.viewer.has_perm('dashboard.change_dashboard'))
        self.assertFalse(self.viewer.has_perm('dashboard.delete_dashboard'))

        self.assertTrue(self.viewer.has_perm('dashboard.view_widget'))
        self.assertFalse(self.viewer.has_perm('dashboard.add_widget'))
        self.assertFalse(self.viewer.has_perm('dashboard.change_widget'))
        self.assertFalse(self.viewer.has_perm('dashboard.delete_widget'))

        self.assertTrue(self.viewer.has_perm('dashboard.view_widgettype'))
        self.assertFalse(self.viewer.has_perm('dashboard.add_widgettype'))
        self.assertFalse(self.viewer.has_perm('dashboard.change_widgettype'))
        self.assertFalse(self.viewer.has_perm('dashboard.delete_widgetype'))

        self.assertTrue(self.viewer.has_perm('dashboard.view_stattype'))
        self.assertFalse(self.viewer.has_perm('dashboard.add_stattype'))
        self.assertFalse(self.viewer.has_perm('dashboard.change_stattype'))
        self.assertFalse(self.viewer.has_perm('dashboard.delete_stattype'))

    def test_viewer_can_view_my_org_share_org(self):
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.my_org_dashboard_share_org.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_view_my_org_share_none(self):
        self.my_org_dashboard_share_none.id
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.my_org_dashboard_share_none.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_can_view_not_my_org_share_all(self):
        self.not_my_org_dashboard_share_all.id
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.not_my_org_dashboard_share_all.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_view_not_my_org_share_org(self):
        self.not_my_org_dashboard_share_all.id
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.not_my_org_dashboard_share_org.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_view_not_my_org_share_none(self):
        self.not_my_org_dashboard_share_all.id
        ''' a viewer can view own org's share_org resource'''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.not_my_org_dashboard_share_none.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
