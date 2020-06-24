from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from institution.models import Institution, InstitutionUser


'''Tests for institution models:
    *Institution
    *InstitutionUser


to run only the app tests:
    /mg.sh "test institution && flake8"
to run only this file
    ./mg.sh "test institution.tests.test_institution_api  && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class InstitutionAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="test@pnsn.org", password="secret")
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        self.institution = Institution.objects.create(name="UW")
        self.institution2 = Institution.objects.create(name="CVO")

        u1 = sample_user("au1@pnsn.org")
        u2 = sample_user("au2@pnsn.org")
        u3 = sample_user("au3@cvo.org")
        self.au1 = InstitutionUser.objects.create(
            user=u1, organization=self.institution)
        self.au2 = InstitutionUser.objects.create(
            user=u2, organization=self.institution)
        self.au3 = InstitutionUser.objects.create(
            user=u3, organization=self.institution2)
        self.institution.organization_users.add(self.au1)
        self.institution.organization_users.add(self.au2)
        self.institution2.organization_users.add(self.au3)

    def test_get_organization(self):
        '''test get on organization'''
        url = reverse('institution:institution-detail',
                      kwargs={'pk': self.institution.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_organization_user(self):
        '''test get institution user'''
        url = reverse('institution:institutionuser-detail',
                      kwargs={'pk': self.au1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_institution_user(self):
        url_institution = reverse('institution:institution-detail',
                                  kwargs={'pk': self.institution.id})
        res = self.client.get(url_institution)
        self.assertEqual(len(res.data['organization_users']), 2)
        url = reverse('institution:institutionuser-list')
        print(url)
        payload = {
            'user': {
                'email': 'testy@pnsn.org'
                # 'firstname': 'testy',
                # 'lastname': 'mctesterson',
                # 'password': "fsadf"
            },
            "organization": self.institution.id,
            'is_admin': False,
        }
        res = self.client.post(url, payload, format='json')
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_get_users_for_organization(self):
        url = reverse('institution:institutionuser-list')
        url += f'?organization={self.institution2.id}'
        print(url)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
