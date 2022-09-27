from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from organization.models import Organization
from squac.test_mixins import sample_user, create_group


'''Tests for organization filters in views.py

to run only the app tests:
    /mg.sh "test organizations && flake8"
to run only this file
    ./mg.sh "test organization.tests.test_organization_filters  && flake8"

'''


class OrganizationFilterTests(TestCase):
    # Tests for organization filters]
    def setUp(self):
        self.client = APIClient()
        self.group_viewer = create_group('viewer', [])
        self.group_reporter = create_group('reporter', [])
        self.group_contributor = create_group('contributor', [])
        self.group_org_admin = create_group("org_admin", [])

        self.org1 = Organization.objects.create(name="UW")
        self.org2 = Organization.objects.create(name="CVO")
        self.staff = sample_user(
            email="test@pnsn.org",
            password="secret",
            organization=self.org1
        )
        self.staff.is_staff = True
        self.client.force_authenticate(self.staff)

        self.org1user = sample_user("1@org1.org", 'secret', self.org1)
        self.org2user = sample_user("2@org2.org", 'secret', self.org2)

    def test_organization_ordering(self):
        '''test organization ordering '''
        url = reverse('organization:organization-list')

        res = self.client.get(url + '?order=name')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertGreater(res.data[1]['name'], res.data[0]['name'])

        res2 = self.client.get(url + '?order=-name')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data), 2)
        self.assertGreater(res2.data[0]['name'], res2.data[1]['name'])
