from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from organization.models import Organization
from dashboard.models import Dashboard

'''Tests for custom dashboard filter in views.py

     ./mg.sh "test dashboard.tests.test_dashboard_filters && flake8"
'''


class PublicDashboardFilterTests(TestCase):
    # Public tests for dashboard filters
    fixtures = ['core_user.json', 'base.json']

    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name='Org')
        self.user = get_user_model().objects.create_user(
            'test@pnsn.org',
            "secret",
            self.organization)
        self.user.is_staff = True
        self.client.force_authenticate(self.user)

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
