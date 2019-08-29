from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from dashboard.models import Dashboard

'''Tests for custom dashboard filter in views.py'''


class PublicDashboardFilterTests(TestCase):
    # Public tests for dashboard filters
    fixtures = ['fixtures_all.json']
    # Fixtures load from fixtures directory in app
    # see README in app/fixutes/README

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=None)

    def test_widget_dashboard_filter(self):
        dashboards = Dashboard.objects.all()
        for d in dashboards:
            url = reverse('dashboard:widget-list')
            url += f'?dashboard={d.id}'
            res = self.client.get(url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            dashboard = Dashboard.objects.get(id=d.id)
            widgets = dashboard.widgets.all()
            self.assertEqual(len(widgets), len(res.data))
            for dict in res.data:
                self.assertEqual(dict['dashboard']['id'], d.id)
