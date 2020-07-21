from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from organization.models import Organization
from squac.test_mixins import sample_user


'''Tests for org models:
    *Org


to run only the app tests:
    /mg.sh "test org && flake8"
to run only this file
    ./mg.sh "test org.tests.test_org_api  && flake8"

'''


class OrganizationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="UW")
        self.org2 = Organization.objects.create(name="CVO")
        self.staff = sample_user(
            email="test@pnsn.org",
            password="secret",
            organization=self.org2)
        self.staff.is_staff = True
        self.client.force_authenticate(self.staff)

        # org1admin = sample_user("au1@pnsn.org",'secret',
        #     self.org, is_org_admin=True
        # )
        # org2User = sample_user("au3@cvo.org", 'secret', self.org2)

    def test_get_organization(self):
        '''test staff get other organization '''
        url = reverse('organization:organization-detail',
                      kwargs={'pk': self.org2.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
