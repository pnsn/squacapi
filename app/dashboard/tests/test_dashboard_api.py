from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric
from nslc.models import Network, Channel, Group
from dashboard.models import Dashboard, Widget
from organization.models import Organization


from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime
import pytz
from squac.test_mixins import sample_user


'''Tests for all dashboard models:
to run only these tests:
 ./mg.sh "test dashboard && flake8"
'''


class UnauthenticatedDashboardApiTests(TestCase):
    '''Test the dashboard api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all requests
        self.client.force_authenticate(user=None)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Metric test',
            code="code123",
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
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
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            user=self.user,
            organization=self.organization
        )

        self.grp.channels.add(self.chan)
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            user=self.user,
            organization=self.organization,
            channel_group=self.grp,
        )
        self.widget = Widget.objects.create(
            name='Test widget',
            dashboard=self.dashboard,
            user=self.user
        )
        self.widget.metrics.add(self.metric)

    def test_dashboard_unauthorized(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_widget_unauthorized(self):
        url = reverse('dashboard:widget-detail', kwargs={'pk': self.widget.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateDashboardAPITests(TestCase):
    '''For authenticated tests in dashboard API'''

    fixtures = ['core_user.json', 'base.json']

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.user.is_staff = True
        self.client.force_authenticate(self.user)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Sample metric',
            code="asdfjcode",
            unit='furlong',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
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
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Sample group',
            user=self.user,
            organization=self.organization
        )
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            user=self.user,
            organization=self.organization,
            properties={
                "window_seconds": 1
            },
            channel_group=self.grp,
        )
        self.widget = Widget.objects.create(
            name='Test widget',
            dashboard=self.dashboard,
            user=self.user
        )

    def test_get_dashboard(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test dashboard')
        self.assertEqual(str(self.dashboard), 'Test dashboard')

    def test_create_dashboard(self):
        url = reverse('dashboard:dashboard-list')
        payload = {
            'name': 'Test dashboard',
            'organization': self.organization.id,
            'channel_group': self.grp.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_get_widget(self):
        url = reverse('dashboard:widget-detail', kwargs={'pk': self.widget.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test widget')
        self.assertEqual(str(self.widget), 'Test widget')

    def test_create_widget(self):
        url = reverse('dashboard:widget-list')
        payload = {
            'name': 'Test widget',
            'dashboard': self.dashboard.id,
            'metrics': [self.metric.id],
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        widget = Widget.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'dashboard':
                self.assertEqual(payload[key], widget.dashboard.id)
            elif key == 'metrics':
                metrics = widget.metrics.all()
                self.assertIn(self.metric, metrics)
            elif key == 'organization':
                self.assertEqual(payload[key],
                                 widget.dashboard.organization.id)
            else:
                self.assertEqual(payload[key], getattr(widget, key))
