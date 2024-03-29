from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from squac.test_mixins import sample_user
from organization.models import Organization
# from organization.backends.tokens import RegistrationTokenGenerator

''' Tests for user api run with. run all tests with

use mg.sh script:
    ./mg.sh "test && flake8"
    or to test this file
    ./mg.sh "test user.tests.test_user_api  && flake8"
'''

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


class PublicUserApiTests(TestCase):
    '''test the users API (public)'''

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_user_unauthorized(self):
        '''test that auth is required for users'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticateApiUser(TestCase):
    fixtures = ['core_user.json', 'base.json']

    '''actually test the auth route'''

    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name='PNSN')

    def test_create_token_success(self):
        '''test token success'''
        sample_user(
            email='test123@pnsn.org',
            password="secret",
            organization=self.organization,
            firstname='your',
            lastname='mom'
        )
        payload = {'email': 'test123@pnsn.org', 'password': "secret"}
        res = self.client.post(CREATE_TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateUserAPITests(TestCase):
    '''test api request that require auth'''
    fixtures = ['core_user.json', 'base.json']

    def setUp(self):
        self.organization = Organization.objects.create(name='PNSN')
        self.user = sample_user(
            email='test@pnsn.org',
            password="secret",
            organization=self.organization,
            firstname='your',
            lastname='mom',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.admin_user = get_user_model().objects.create_superuser(
            email='adminy@pnsn.org',
            password='admin_pass',
            organization=self.organization,
        )

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

    def test_retrieve_profile_success(self):
        '''test retrieving profile for logged in user'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_post_me_not_allowed(self):
        '''test that post is not allowed on the me url'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''test updating the user profile for authenticated user'''
        payload = {
            'firstname': 'cool_name',
            'password': "secret",
            'organization': self.organization.id
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.firstname, payload['firstname'])
        self.assertTrue(self.user.check_password, payload['password'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_no_user(self):
        '''test token is not created if user doesn't exist'''
        payload = {
            'email': 'test1@pnsn.org',
            'password': "nouser",
            'organization': self.organization.id
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_invalid_credentials(self):
        '''test that token is not created if invalid creds are given'''
        sample_user(email="test2@pnsn.org", password='secretpass',
                    organization=self.organization)
        payload = {
            'email': 'test2@pnsn.org',
            'password': "wrongpass",
            'organization': self.organization.id,
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        '''test that email and password are required'''
        payload = {
            'email': "",
            "password": "",
            'organization': self.organization.id}
        res = self.client.post(CREATE_TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post

    def test_create_valid_user_success(self):
        '''test creating user with valid payload is succssful if admin'''

        payload = {
            'email': 'test3@test.com',
            'organization': self.organization.id,
            'firstname': 'some',
            'lastname': 'name',
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res = self.admin_client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(
            email=payload['email'])
        self.assertEqual(user.firstname, payload['firstname'])
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''test creating user that exists fails'''
        payload = {
            'email': "test@test.com",
            'password': 'supersecret',
            'organization': self.organization.id
        }
        # sample_user(**payload)

        res = self.admin_client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''the password must be more than 5 chars'''

        # create user
        payload = {
            'email': "test@test.com",
            'firstname': 'name',
            'lastname': 'name',
            'organization': self.organization.id
        }
        res = self.admin_client.post(CREATE_USER_URL, payload)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertTrue(user_exists)

        update_payload = {
            'password': 'js',
        }

        res = self.client.patch(ME_URL, update_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_groups(self):
        '''test retrieve perm groups'''
        url = reverse('user:group-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
