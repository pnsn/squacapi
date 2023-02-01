from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from organization.models import Organization
from squac.test_mixins import sample_user, create_group


'''Tests for org models:
    *Org


to run only the app tests:
    /mg.sh "test organizations && flake8"
to run only this file
    ./mg.sh "test organization.tests.test_organization_api  && flake8"

'''


class OrganizationAPITests(TestCase):

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

    def test_get_organization(self):
        '''test staff get other organization '''
        url = reverse('organization:organization-detail',
                      kwargs={'pk': self.org2.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_organization_user(self):
        '''test get org user'''
        url = reverse('organization:organizationuser-detail',
                      kwargs={'pk': self.org1user.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_org_user_new_user(self):
        '''create org_user for new user'''
        url_org = reverse('organization:organization-detail',
                          kwargs={'pk': self.org1.id})
        res = self.client.get(url_org)
        self.assertEqual(len(res.data['users']), 2)
        url = reverse('organization:organizationuser-list')
        payload = {
            'email': 'testy@pnsn.org',
            "organization": self.org1.id,
            "groups": [
                self.group_contributor.name
            ],
            "firstname": "first",
            "lastname": "last"
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # check if new user shows in org
        res = self.client.get(url_org)
        self.assertEqual(len(res.data['users']), 3)

        # now try create again, should fail on uniqueness
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_org_user(self):
        '''change org user to admin
        '''
        user = self.org1user
        self.assertFalse(user.is_org_admin)
        url = reverse('organization:organizationuser-detail', args=[user.id])

        payload = {
            'email': user.email,
            "organization": self.org1.id,
            'is_org_admin': True,
            'firstname': "Seymore",
            'lastname': 'things',
            'groups': [
                self.group_contributor.name
            ]
        }
        res = self.client.patch(url, payload, format='json')

        # should now have 4 groups since contrib needs viewer and reporter
        # and we made admin
        self.assertEqual(res.data['firstname'], 'Seymore')
        self.assertEqual(len(res.data['groups']), 4)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_org_admin'])
