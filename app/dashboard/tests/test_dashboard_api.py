from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from measurement.models import Metric
from nslc.models import Network, Station, Channel, Group
from dashboard.models import Dashboard, Widget, WidgetType

from rest_framework.test import APIClient
from rest_framework import status


'''Tests for all measurement models:
to run only these tests:
 ./mg.sh "test measurement && flake8"
'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class PublicMeasurementApiTests(TestCase):
    '''Test the dashboard api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all public tests
        self.client.force_authenticate(user=None)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Metric test',
            unit='meter',
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        self.sta = Station.objects.create(
            code='RCM',
            name="Camp Muir",
            network=self.net,
            user=self.user
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            loc="--",
            station=self.sta,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user
        )
        self.grp = Group.objects.create(
            name='Test group',
            is_public=True,
            user=self.user
        )
        self.grp.channels.add(self.chan)
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            group=self.grp,
            user=self.user
        )
        self.widtype = WidgetType.objects.create(
            name='Test widget type',
            type='Some type',
            user=self.user
        )
        self.widget = Widget.objects.create(
            name='Test widget',
            dashboard=self.dashboard,
            widgettype=self.widtype,
            user=self.user
        )
        self.widget.metrics.add(self.metric)
#         self.threshold = Threshold.objects.create(
#             name="Threshold test",
#             min=2.1,
#             max=3.5,
#             metricgroup=self.metricgroup,
#             user=self.user
#         )
#         self.alarm = Alarm.objects.create(
#             name='Alarm test',
#             period=2,
#             num_period=3,
#             threshold=self.threshold,
#             user=self.user
#         )
#         self.trigger = Trigger.objects.create(
#             count=0,
#             alarm=self.alarm,
#             user=self.user
#         )

    def test_dashboard_res_and_str(self):
        url = reverse(
            'dashboard:dashboard-detail',
            kwargs={'pk': self.dashboard.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test dashboard')
        self.assertEqual(str(self.dashboard), 'Test dashboard')

    def test_widget_type_res_and_str(self):
        url = reverse(
            'dashboard:widgettype-detail',
            kwargs={'pk': self.widtype.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test widget type')
        self.assertEqual(str(self.widtype), 'Test widget type')

    def test_widget_res_and_str(self):
        url = reverse('dashboard:widget-detail', kwargs={'pk': self.widget.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Test widget')
        self.assertEqual(str(self.widget), 'Test widget')

#     def test_threshold_res_and_str(self):
#         url = reverse(
#             'measurement:threshold-detail',
#             kwargs={'pk': self.threshold.id}
#         )
#         res = self.client.get(url)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data['name'], 'Threshold test')
#         self.assertEqual(str(self.threshold), 'Threshold test')

#     def test_threshold_post_unauth(self):
#         url = reverse('measurement:threshold-list')
#         payload = {
#             'name': 'Test',
#             'min': 2.1,
#             'max': 2.2,
#             'metricgroup': self.metricgroup.id
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_alarm_res_and_str(self):
#         url = reverse(
#             'measurement:alarm-detail',
#             kwargs={'pk': self.alarm.id}
#         )
#         res = self.client.get(url)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(res.data['name'], 'Alarm test')
#         self.assertEqual(str(self.alarm), 'Alarm test')

#     def test_alarm_post_unauth(self):
#         url = reverse('measurement:alarm-list')
#         payload = {
#             'name': 'Alarm test',
#             'period': 2,
#             'num_period': 3,
#             'threshold': self.threshold
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_trigger_res_and_str(self):
#         url = reverse(
#             'measurement:trigger-detail',
#             kwargs={'pk': self.trigger.id}
#         )
#         res = self.client.get(url)
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertEqual(str(self.trigger), 'Alarm: Alarm test Count: 0')

#     def test_trigger_post_unauth(self):
#         url = reverse('measurement:trigger-list')
#         payload = {
#             'count': 0,
#             'alarm': self.alarm.id
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    '''For authenticated tests in dashboard API'''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        timezone.now()
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
        )
        self.sta = Station.objects.create(
            code='RCM',
            name="Camp Muir",
            network=self.net,
            user=self.user
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            loc="--",
            station=self.sta,
            lat=45,
            lon=-122,
            elev=0,
            user=self.user
        )
        self.grp = Group.objects.create(
            name='Sample group',
            is_public=True,
            user=self.user
        )
        self.dashboard = Dashboard.objects.create(
            name='Test dashboard',
            group=self.grp,
            user=self.user
        )
        self.widtype = WidgetType.objects.create(
            name='Test widget type',
            type='Some type',
            user=self.user
        )
#         self.threshold = Threshold.objects.create(
#             name="Sample threshold",
#             min=2.1,
#             max=3.5,
#             metricgroup=self.metricgroup,
#             user=self.user
#         )
#         self.alarm = Alarm.objects.create(
#             name='Alarm test',
#             period=2,
#             num_period=3,
#             threshold=self.threshold,
#             user=self.user
#         )

    def test_create_dashboard(self):
        url = reverse('dashboard:dashboard-list')
        payload = {'name': 'Test dashboard', 'group': self.grp.id}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        dashboard = Dashboard.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'group':
                self.assertEqual(payload[key], dashboard.group.id)
            else:
                self.assertEqual(payload[key], getattr(dashboard, key))

    def test_create_widgettype(self):
        url = reverse('dashboard:widgettype-list')
        payload = {'name': "Test widget type", "type": "Type"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        widtype = WidgetType.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(widtype, key))

    def test_create_widget(self):
        url = reverse('dashboard:widget-list')
        payload = {
            'name': 'Test widget',
            'dashboard': self.dashboard.id,
            'widgettype': self.widtype.id,
            'metrics': [self.metric.id]
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        widget = Widget.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'dashboard':
                self.assertEqual(payload[key], widget.dashboard.id)
            elif key == 'widgettype':
                self.assertEqual(payload[key], widget.widgettype.id)
            elif key == 'metrics':
                metrics = widget.metrics.all()
                self.assertIn(self.metric, metrics)
            else:
                self.assertEqual(payload[key], getattr(widget, key))

#     def test_create_threshold(self):
#         url = reverse('measurement:threshold-list')
#         payload = {
#             'name': 'Test',
#             'min': 2.1,
#             'max': 2.2,
#             'metricgroup': self.metricgroup.id
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         threshold = Threshold.objects.get(id=res.data['id'])
#         for key in payload.keys():
#             if key == 'metricgroup':
#                 self.assertEqual(payload[key], threshold.metricgroup.id)
#             else:
#                 self.assertEqual(payload[key], getattr(threshold, key))

#     def test_create_alarm(self):
#         url = reverse('measurement:alarm-list')
#         payload = {
#             'name': 'Alarm test',
#             'period': 2,
#             'num_period': 3,
#             'threshold': self.threshold.id
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         alarm = Alarm.objects.get(id=res.data['id'])
#         for key in payload.keys():
#             if key == 'threshold':
#                 self.assertEqual(payload[key], alarm.threshold.id)
#             else:
#                 self.assertEqual(payload[key], getattr(alarm, key))

#     def test_create_trigger(self):
#         url = reverse('measurement:trigger-list')
#         payload = {
#             'count': 0,
#             'alarm': self.alarm.id
#         }
#         res = self.client.post(url, payload)
#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         trigger = Trigger.objects.get(id=res.data['id'])
#         for key in payload.keys():
#             if key == 'alarm':
#                 self.assertEqual(payload[key], trigger.alarm.id)
#             else:
#                 self.assertEqual(payload[key], getattr(trigger, key))
