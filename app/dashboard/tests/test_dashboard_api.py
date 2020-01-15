from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric, Threshold
from nslc.models import Network, Channel, Group
from dashboard.models import Dashboard, Widget, WidgetType, StatType

from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime
import pytz


'''Tests for all measurement models:
to run only these tests:
 ./mg.sh "test dashboard && flake8"
'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class UnathenticatedMeasurementApiTests(TestCase):
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
        self.grp = Group.objects.create(
            name='Test group',
            is_public=True,
            user=self.user
        )
        self.grp.channels.add(self.chan)
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            user=self.user
        )
        self.widtype = WidgetType.objects.create(
            name='Test widget type',
            type='Some type',
            user=self.user
        )
        self.stattype = StatType.objects.create(
            name="Average",
            type="ave",
            user=self.user
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
            user=self.user,
            channel_group=self.grp
        )
        self.widget.metrics.add(self.metric)

    def test_dashboard_unauthorized(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_widget_type_unauthorized(self):
        url = reverse(
            'dashboard:widgettype-detail',
            kwargs={'pk': self.widtype.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_widget_unauthorized(self):
        url = reverse('dashboard:widget-detail', kwargs={'pk': self.widget.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    '''For authenticated tests in dashboard API'''

    fixtures = ['fixtures_all.json']

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
        self.grp = Group.objects.create(
            name='Sample group',
            is_public=True,
            user=self.user
        )
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            user=self.user
        )
        self.widtype = WidgetType.objects.create(
            name='Test widget type',
            type='Some type',
            user=self.user
        )
        self.stattype = StatType.objects.create(
            name="Maxeo",
            type="max",
            user=self.user
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
            user=self.user,
            channel_group=self.grp,

        )

        self.threshold = Threshold.objects.create(
            widget=self.widget,
            metric=self.metric,
            minval=9.0,
            maxval=10.0,
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
        for widget in res.data['widgets']:
            self.assertEqual(widget, self.widget.id)

    def test_create_dashboard(self):
        url = reverse('dashboard:dashboard-list')
        payload = {'name': 'Test dashboard'}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        dashboard = Dashboard.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(dashboard, key))

    def test_get_widget_type(self):
        url = reverse(
            'dashboard:widgettype-detail',
            kwargs={'pk': self.widtype.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test widget type')
        self.assertEqual(str(self.widtype), 'Test widget type')

    def test_create_widgettype(self):
        url = reverse('dashboard:widgettype-list')
        payload = {'name': "Test widget type", "type": "Type"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        widtype = WidgetType.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(widtype, key))

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
            'widgettype': self.widtype.id,
            'stattype': self.stattype.id,
            'columns': 6,
            'rows': 3,
            'x_position': 1,
            'y_position': 1,
            'metrics': [self.metric.id],
            'channel_group': self.grp.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        widget = Widget.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'dashboard':
                self.assertEqual(payload[key], widget.dashboard.id)
            elif key == 'widgettype':
                self.assertEqual(payload[key], widget.widgettype.id)
            elif key == 'stattype':
                self.assertEqual(payload[key], widget.stattype.id)
            elif key == 'metrics':
                metrics = widget.metrics.all()
                self.assertIn(self.metric, metrics)
            elif key == 'channel_group':
                self.assertEqual(payload[key], widget.channel_group.id)
            else:
                self.assertEqual(payload[key], getattr(widget, key))

    def test_get_threshold(self):
        url = reverse('measurement:threshold-detail',
                      kwargs={'pk': self.threshold.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(float(res.data['maxval']), 10.0)
        self.assertEqual(float(res.data['minval']), 9.0)

    # def test_create_threshold(self):
    #     url = reverse('measurement:threshold-list')
    #     payload = {
    #         'maxval': 10.0,
    #         'minval': 9.0,
    #         'widget': self.widget.id,
    #         'metric': self.metric.id
    #     }
    #     res = self.client.post(url, payload)
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
