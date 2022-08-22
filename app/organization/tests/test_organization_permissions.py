from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from organization.models import Organization
from squac.test_mixins import sample_user, create_group


'''Tests for org models:
    *Org


to run only the app tests:
    /mg.sh "test org && flake8"
to run only this file
    ./mg.sh "test organization.tests.test_organization_permissions && flake8"

'''


'''
only admins can edit orgs
Org Admins cav view orgs
Org Admins can edit org users
Org members can view orgs and org users


'''


class OrganizationAPITests(TestCase):

    # model permissions
    ORGANIZATION_ADMIN_PERMISSIONS = [
        'change_organization',
        'add_user',
        'change_user'
    ]

    VIEWER_PERMISSIONS = [
        'view_organization',
        'view_user'
    ]

    def setUp(self):
        self.org_admin_group = create_group(
            'org_admin',
            self.ORGANIZATION_ADMIN_PERMISSIONS
        )
        self.group_viewer = create_group(
            'viewer', self.VIEWER_PERMISSIONS
        )

        self.group_reporter = create_group('reporter', [])
        self.group_contributor = create_group('contributor', [])

        self.org1 = Organization.objects.create(name="UW")
        self.org2 = Organization.objects.create(name="CVO")

        self.org1_member_client = APIClient()
        self.org2_member_client = APIClient()
        self.org1_admin_client = APIClient()

        self.org1_member = sample_user("member@org1.org", 'secret', self.org1)
        self.org2_member = sample_user("member@org2.org", 'secret', self.org2)
        self.org1_admin = sample_user("admin@org1.org", 'secret', self.org1,
                                      is_org_admin=True)
        # add obj model permissions
        self.org1_member.groups.add(self.group_viewer)
        self.org2_member.groups.add(self.group_viewer)
        self.org1_admin.groups.add(self.org_admin_group)
        self.org1_admin.groups.add(self.group_viewer)

        # authenticate
        self.org1_member_client.force_authenticate(self.org1_member)
        self.org2_member_client.force_authenticate(self.org2_member)
        self.org1_admin_client.force_authenticate(self.org1_admin)

    def test_org_admin_perms(self):
        '''org admins can:

            *add/change_organizatins
            *view/add/change/delete org users
        '''
        self.assertTrue(self.org1_admin.has_perm(
            'organization.view_organization'))
        self.assertFalse(self.org1_admin.has_perm(
            'organization.add_organization'))
        self.assertTrue(self.org1_admin.has_perm(
            'organization.change_organization'))
        self.assertFalse(self.org1_admin.has_perm(
            'organization.delete_organization'))

        self.assertTrue(self.org1_admin.has_perm('core.view_user'))
        self.assertTrue(self.org1_admin.has_perm('core.add_user'))
        self.assertTrue(self.org1_admin.has_perm('core.change_user'))
        self.assertFalse(self.org1_admin.has_perm('core.delete_user'))

    def test_org_member_perms(self):
        '''org members can:

            *view_organizations
            *view users
        '''
        self.assertTrue(self.org1_member.has_perm(
            'organization.view_organization'))
        self.assertFalse(self.org1_member.has_perm(
            'organization.add_organization'))
        self.assertFalse(self.org1_member.has_perm(
            'organization.change_organization'))
        self.assertFalse(self.org1_member.has_perm(
            'organization.delete_organization'))

        self.assertTrue(self.org1_member.has_perm('core.view_user'))
        self.assertFalse(self.org1_member.has_perm('core.add_user'))
        self.assertFalse(self.org1_member.has_perm('core.change_user'))
        self.assertFalse(self.org1_member.has_perm('core.delete_user'))

    def test_org_admin_can_update_org(self):
        '''test org admin update org page'''
        url = reverse('organization:organization-detail', args=[self.org1.id])
        payload = {
            'name': "new_name",
            "description": "new description"
        }
        res = self.org1_admin_client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_member_can_view_own_org(self):
        ''' test member view own org page'''
        url = reverse('organization:organization-detail', args=[self.org1.id])
        res = self.org1_member_client.get(url, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_member_can_view_other_org(self):
        '''test member cannot view other org page'''
        url = reverse('organization:organization-detail', args=[self.org1.id])
        res = self.org2_member_client.get(url, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_create_org_user_new_user(self):
        '''org admin should be able to create org_user'''
        url = reverse('organization:organizationuser-list')
        payload = {
            'email': 'testy@pnsn.org',
            "organization": self.org1.id,
            'groups': [self.group_reporter.id],
            "firstname": "first",
            "lastname": "last"
        }
        res = self.org1_admin_client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_cannot_create_org_other_org_member(self):
        '''org admin should be able to create org_user'''
        url = reverse('organization:organizationuser-list')
        payload = {
            'email': 'testy@pnsn.org',
            "organization": self.org2.id
        }
        res = self.org1_admin_client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_update_org_user(self):
        '''change org user to admin
        '''
        user = self.org1_member
        self.assertFalse(user.is_org_admin)
        url = reverse('organization:organizationuser-detail', args=[user.id])
        payload = {
            'email': user.email,
            "organization": self.org1.id,
            'is_org_admin': True
        }
        res = self.org1_admin_client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_org_admin'])

    def test_admin_cannot_update_other_org_member(self):
        '''org admin should not be able to update other org user
        '''
        user = self.org2_member
        self.assertFalse(user.is_org_admin)
        url = reverse('organization:organizationuser-detail', args=[user.id])
        payload = {
            'email': user.email,
            "organization": self.org2.id,
            'is_org_admin': True
        }
        res = self.org1_admin_client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
