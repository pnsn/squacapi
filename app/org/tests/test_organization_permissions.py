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
    ./mg.sh "test org.tests.test_organization_permissions  && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class OrganizationAPITests(TestCase):

    def setUp(self):
        self.clientAdmin = APIClient()
        self.clientUser = APIClient()
        self.admin = sample_user("admin@pnsn.org")
        self.user = sample_user(email="user@pnsn.org")
        self.other_user = sample_user('other_org_user@other.org')
        self.clientAdmin.force_authenticate(self.admin)
        self.clientUser.force_authenticate(self.user)
        self.org = Organization.objects.create(name="PNSN")
        self.other_org = Organization.objects.create(name="Other")
        self.orgAdmin = OrganizationUser.objects.create(
            user=self.admin, organization=self.org, is_admin=True)
        self.orgUser = OrganizationUser.objects.create(
            user=self.user, organization=self.org, is_admin=False)
        self.org.organization_users.add(self.orgAdmin)
        self.org.organization_users.add(self.orgUser)
        self.other_org_user = OrganizationUser.create(
            user=self.other_org, organization=self.other_org)

    # def test_get_organization(self):
    #     '''both user and admin should be able to view org'''
    #     url = reverse('org:organization-detail',
    #                   kwargs={'pk': self.org.id})
    #     res = self.clientAdmin.get(url)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     res = self.clientUser.get(url)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)

    # def test_get_organization_user(self):
    #     '''both user and admin should be able to view orguser'''
    #     url = reverse('org:organizationuser-detail',
    #                   kwargs={'pk': self.orgAdmin.id})
    #     res = self.clientAdmin.get(url)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     res = self.clientUser.get(url)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)

    # def test_create_org_user_new_user(self):
    #     '''create org_user for existing user'''
    #     url_org = reverse('org:organization-detail',
    #                       kwargs={'pk': self.org.id})
    #     res = self.clientAdmin.get(url_org)
    #     self.assertEqual(len(res.data['organization_users']), 2)
    #     url = reverse('org:organizationuser-list')

    #     payload = {
    #         'user': {
    #             'email': 'testy@pnsn.org'
    #         },
    #         "organization": self.org.id,
    #         'is_admin': False,
    #     }
    #     # member should not be able to create user
    #     res = self.clientUser.post(url, payload, format='json')
    #     self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    #     res = self.clientAdmin.post(url, payload, format='json')
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    #     # now try create again, should fail on uniqueness
    #     res = self.clientAdmin.post(url, payload, format='json')
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_org_user_existing_user(self):
        '''user exists as org user of another group
            should be able to add to another institiution
        '''
        # user = self.admin
        existing_user = sample_user("exisiting@pnsn.org")
        self.assertEqual(len(existing_user.organizations_organization.all()), 2)
        url = reverse('org:organizationuser-list')
        payload = {
            'user': {
                'email': existing_user.email
            },
            "organization": self.org.id,
            'is_admin': False,
        }
        res = self.clientAdmin.post(url, payload, format='json')
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(existing_user.organizations_organization.all()), 2)

    # def test_update_org_user(self):
    #     '''change org user to admin
    #     '''
    #     user = self.admin
    #     self.assertFalse(self.orgUser.is_admin)
    #     url = reverse('org:organizationuser-detail', args=[self.orgUser.id])
    #     payload = {
    #         'user': {
    #             'email': user.email
    #         },
    #         "organization": self.org.id,
    #         'is_admin': True
    #     }
    #     res = self.clientAdmin.put(url, payload, format='json')
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #     self.assertTrue(res.data['is_admin'])

    # def test_get_users_for_organization(self):
    #     url = reverse('org:organizationuser-list')
    #     url += f'?organization={self.org.id}'
    #     res = self.clientAdmin.get(url)
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(res.data), 1)
