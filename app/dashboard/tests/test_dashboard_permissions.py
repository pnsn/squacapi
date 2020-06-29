from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as UserGroup, Permission
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime
import pytz
from dashboard.models import Dashboard, Widget, WidgetType, StatType
from measurement.models import Metric
from nslc.models import Network, Channel, Group
from organizations.models import Organization


'''
    to run this file only
    ./mg.sh "test dashboard.tests.test_dashboard_permissions && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


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
            user=self.other
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
        self.grp = Group.objects.create(
            name='Test group',
            is_public=True,
            user=self.reporter
        )
        self.grp.channels.add(self.chan)
        self.organization = Organization.objects.create(
            name='PNSN',
            slug='pnsn'
        )
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            user=self.reporter,
            organization=self.organization
        )
        self.dashboard_other = Dashboard.objects.create(
            name='Test dashboard2',
            user=self.other,
            is_public=True,
            organization=self.organization
        )
        self.dashboard_other_private = Dashboard.objects.create(
            name='Test dashboard2',
            user=self.other,
            is_public=False,
            organization=self.organization
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
            dashboard=self.dashboard,
            widgettype=self.widtype,
            stattype=self.stattype,
            columns=6,
            rows=3,
            x_position=1,
            y_position=1,
            user=self.reporter,
            channel_group=self.grp,
            is_public=True,
            organization=self.organization
        )

        self.widget_other = Widget.objects.create(
            name='Test widget2',
            dashboard=self.dashboard,
            widgettype=self.widtype,
            stattype=self.stattype,
            columns=6,
            rows=3,
            x_position=1,
            y_position=1,
            user=self.other,
            channel_group=self.grp,
            is_public=True,
            organization=self.organization
        )

        self.widget_other_private = Widget.objects.create(
            name='Test widget3',
            dashboard=self.dashboard,
            widgettype=self.widtype,
            stattype=self.stattype,
            columns=6,
            rows=3,
            x_position=1,
            y_position=1,
            user=self.other,
            channel_group=self.grp,
            is_public=False,
            organization=self.organization
        )

        self.widget.metrics.add(self.metric)

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

    # #### dashboard tests ####
    def test_viewer_reporter_view_public_dashboard(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard_other.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_view_private_dashboard(self):
        '''reporter should be able to see own private dash
           viewer should not
        '''
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertNotEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_view_dashboard_list(self):
        url = reverse('dashboard:dashboard-list')
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(len(res.data), 1)

        res = self.reporter_client.get(url)
        self.assertEqual(len(res.data), 2)

    def test_viewer_reporter_create_dashboard(self):
        url = reverse('dashboard:dashboard-list')
        payload = {
            'name': 'Test dashboard',
            'organization': self.organization.id
        }
        # viewer
        res = self.viewer_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # reporter
        res = self.reporter_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_reporter_delete_dashboard(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        res = self.viewer_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_reporter_cannot_delete_other_dashboard(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard_other.id}
        )
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # #### widget tests ####
    def test_viewer_reporter_view_widget(self):
        url = reverse(
            'dashboard:widget-detail',
            kwargs={'pk': self.widget.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_view_widget_list(self):
        url = reverse('dashboard:widget-list')
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(len(res.data), 2)

        res = self.reporter_client.get(url)
        self.assertEqual(len(res.data), 2)

    def test_viewer_reporter_create_widget(self):
        url = reverse('dashboard:widget-list')
        payload = {
            'name': 'Test widget',
            'dashboard': self.dashboard.id,
            'widgettype': self.widtype.id,
            'stattype': self.stattype.id,
            'columns': 6,
            'rows': 3,
            'x_position': 1,
            'y_position': 1,
            'metrics': [self.metric.id],
            'channel_group': self.grp.id,
            'organization': self.organization.id
        }
        # viewer
        res = self.viewer_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # reporter
        res = self.reporter_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_reporter_delete_widget(self):
        url = reverse(
            'dashboard:widget-detail',
            kwargs={'pk': self.widget.id}
        )
        res = self.viewer_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_reporter_cannot_delete_other_widget(self):
        url = reverse(
            'dashboard:widget-detail',
            kwargs={'pk': self.widget_other.id}
        )
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
