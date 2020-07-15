from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from organizations.models import (Organization, OrganizationUser)

'''Tests for org models:
    *Org
    *OrgUser


to run only the app tests:
    /mg.sh "test org && flake8"
to run only this file
    ./mg.sh "test org.tests.test_org_api  && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class OrganizationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="test@pnsn.org", password="secret")
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        self.org = Organization.objects.create(name="UW")
        self.org2 = Organization.objects.create(name="CVO")

        u1 = sample_user("au1@pnsn.org")
        u2 = sample_user("au2@pnsn.org")
        u3 = sample_user("au3@cvo.org")
        self.au1 = OrganizationUser.objects.create(
            user=u1, organization=self.org)
        self.au2 = OrganizationUser.objects.create(
            user=u2, organization=self.org)
        self.au3 = OrganizationUser.objects.create(
            user=u3, organization=self.org2)
        self.org.organization_users.add(self.au1)
        self.org.organization_users.add(self.au2)
        self.org2.organization_users.add(self.au3)

    def test_get_organization(self):
        '''test get on organization'''
        url = reverse('org:organization-detail',
                      kwargs={'pk': self.org.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_organization_user(self):
        '''test get org user'''
        url = reverse('org:organizationuser-detail',
                      kwargs={'pk': self.au1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_org_user_new_user(self):
        '''create org_user for existing user'''
        url_org = reverse('org:organization-detail',
                          kwargs={'pk': self.org.id})
        res = self.client.get(url_org)
        self.assertEqual(len(res.data['organization_users']), 2)
        url = reverse('org:organizationuser-list')

        payload = {
            'user': {
                'email': 'testy@pnsn.org'
            },
            "organization": self.org.id,
            'is_admin': False,
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # now try create again, should fail on uniqueness
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_org_user_existing_user(self):
        '''user exists as org user of another group
            should be able to add to another institiution
        '''
        user = self.au3.user
        self.assertEqual(len(user.organizations_organization.all()), 1)
        url = reverse('org:organizationuser-list')
        payload = {
            'user': {
                'email': user.email
            },
            "organization": self.org.id,
            'is_admin': False,
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(user.organizations_organization.all()), 2)

    def test_update_org_user(self):
        '''change org user to admin
        '''
        user = self.au3.user
        self.assertFalse(self.au3.is_admin)
        url = reverse('org:organizationuser-detail', args=[self.au3.id])
        payload = {
            'user': {
                'email': user.email
            },
            "organization": self.org.id,
            'is_admin': True
        }
        res = self.client.put(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_admin'])

    def test_get_users_for_organization(self):
        url = reverse('org:organizationuser-list')
        url += f'?organization={self.org2.id}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
