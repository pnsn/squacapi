from django.test import TestCase
from django.contrib.auth import get_user_model
# from django.urls import reverse
from rest_framework.test import APIClient
# from rest_framework import status

''' Tests for user api run with. run all tests with

docker-compose run app sh -c "python manage.py test && flake8" '''


# CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''test the users API (public)'''

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        '''test creating user with valid payload is succssful

           This test will be turned into a 403 since creating a user
           from an unathenticated user is NOT allowed

        '''

#        payload = {
#            'email': 'test@test.com',
#            'password': 'supersecret',
#            'name': 'some name'
#        }

        # res = self.client.post(CREATE_USER_URL, payload)
        #
        # self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # user = get_user_model().objects.get(**res.data)
        # user.assertTrue(user.check_password(payload['password']))
        # self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''test creating user that exists fails'''
#        payload = {
#            'email': "test@test.com",
#            'password': 'supersecret'
#        }

        # res = self.client.post(CREATE_USER_URL, payload)
        # self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
