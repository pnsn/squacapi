from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from organizations.backends.tokens import RegistrationTokenGenerator

''' Tests for user api run with. run all tests with

docker-compose run app sh -c "python manage.py test && flake8"
or use mg.sh script:
    ./mg.sh "test && flake8"
'''

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''test the users API (public)'''

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_user_unauthorized(self):
        '''test that auth is required for users'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticateApiUser(TestCase):
    '''actually test the auth route'''

    def setUp(self):
        self.client = APIClient()

    def test_create_token_success(self):
        '''test token success'''
        create_user(
            email='test123@pnsn.org',
            password="secret",
            firstname='your',
            lastname='mom'
        )
        payload = {'email': 'test123@pnsn.org', 'password': "secret"}
        res = self.client.post(CREATE_TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class ActivateUser(TestCase):
    ''' user activation by invitation token'''

    def setUp(self):
        self.client = APIClient()
        self.invited_user = create_user(
            email='inactive@pnsn.org',
            password="secret",
            firstname='blank',
            lastname='blank',
            is_active=False
        )

    def test_activate_user_invalid_token(self):
        url = reverse('user:activate_user')
        payload = {
            'email': self.invited_user.email,
            'password': 'superdupersecret',
            'firstname': 'your',
            'lastname': 'mom',
            'token': 'invalid token'
        }
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_activate_user_valid_token(self):
        token = RegistrationTokenGenerator().make_token(self.invited_user)

        url = reverse('user:activate_user')

        payload = {
            "email": self.invited_user.email,
            "password": 'superdupersecret',
            "firstname": 'your',
            "lastname": 'mom',
            "token": token
        }
        self.assertFalse(self.invited_user.is_active)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        updated_user = get_user_model().objects.get(
            email=self.invited_user.email)
        self.assertTrue(updated_user.is_active)


class PrivateUserAPITests(TestCase):
    '''test api request that require auth'''

    def setUp(self):
        self.user = create_user(
            email='test@pnsn.org',
            password="secret",
            firstname='your',
            lastname='mom',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

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
        payload = {'firstname': 'cool_name', 'password': "secret"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.firstname, payload['firstname'])
        self.assertTrue(self.user.check_password, payload['password'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_no_user(self):
        '''test token is not created if user doesn't exist'''
        payload = {'email': 'test1@pnsn.org', 'password': "nouser"}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_invalid_credentials(self):
        '''test that token is not created if invalid creds are given'''
        create_user(email="test2@pnsn.org", password='secretpass')
        payload = {'email': 'test2@pnsn.org', 'password': "wrongpass"}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        '''test that email and password are required'''
        payload = {'email': "", "password": ""}
        res = self.client.post(CREATE_TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res = self.client.post

    def test_create_valid_user_success(self):
        '''test creating user with valid payload is succssful'''

        payload = {
            'email': 'test3@test.com',
            'password': 'supersecret',
            'firstname': 'some',
            'lastname': 'name',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # user = get_user_model().objects.get(**res.data)
        user = get_user_model().objects.get(
            email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''test creating user that exists fails'''
        payload = {
            'email': "test@test.com",
            'password': 'supersecret'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''the password must be more than 5 chars'''

        payload = {'email': "test.test.com", 'password': 'js'}

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
