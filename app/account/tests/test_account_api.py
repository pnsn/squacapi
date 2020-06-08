from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from account.models import Account, AccountUser


'''Tests for account models:
    *Account
    *AccountUser


to run only the app tests:
    /mg.sh "test account && flake8"
to run only this file
    ./mg.sh "test account.tests.test_account_api  && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class AccountAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="test@pnsn.org", password="secret")
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        self.account = Account.objects.create(name="UW")
        u1 = sample_user("au1@pnsn.org")
        u2 = sample_user("au2@pnsn.org")
        self.au1 = AccountUser.objects.create(
            user=u1, organization=self.account)
        self.au2 = AccountUser.objects.create(
            user=u2, organization=self.account)
        self.account.organization_users.add(self.au1)
        self.account.organization_users.add(self.au2)

    def test_get_organization(self):
        '''test get on organization'''
        url = reverse('account:account-detail',
                      kwargs={'pk': self.account.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_organization_user(self):
        '''test get account user'''
        url = reverse('account:accountuser-detail',
                      kwargs={'pk': self.au1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_account_user(self):
        url_account = reverse('account:account-detail',
                              kwargs={'pk': self.account.id})
        res = self.client.get(url_account)
        self.assertEqual(len(res.data['organization_users']), 2)
        url = reverse('account:accountuser-list')
        print(url)
        payload = {
            'user': {
                'email': 'testy@pnsn.org',
                'firstname': 'testy',
                'lastname': 'mctesterson',
                'password': "fsadf"
            },
            "organization": self.account.id,
            'is_admin': False,
        }
        res = self.client.post(url, payload, format='json')
        print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    
