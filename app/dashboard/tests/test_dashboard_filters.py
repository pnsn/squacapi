from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from dashboard.models import Dashboard

'''Tests for custom dashboard filter in views.py'''


class PublicDashboardFilterTests(TestCase):
    # Public tests for dashboard filters
    fixtures = ['dashboard_tests.json']
    # Fixtures load from fixtures directory in dashboard
    # to dump data to a dashboard folder run:
    # ./mg.sh "dumpdata --indent=2 >> dashboard/fixtures/file.json"

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=None)

    def test_widget_dashboard_filter(self):
        dashboards = Dashboard.objects.all()
        for d in dashboards:
            url = 'http://localhost:8000/v1.0/dashboard/widgets/?dashboard='
            url += str(d.id)
            res = self.client.get(url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            dashboard = Dashboard.objects.get(id=d.id)
            widgets = dashboard.widgets.all()
            self.assertEqual(len(widgets), len(res.data))
            for dict in res.data:
                self.assertEqual(dict['dashboard'], d.id)