import base64
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient
from squac.test_mixins import sample_user
from organization.models import Organization
from invite.models import InviteToken
from datetime import timedelta

'''
 To run these tests
 ./mg.sh "test invite.tests.test_invite_api && flake8"
'''


class InviteTokenApiTests(TestCase):
    '''test token creation'''
    def setUp(self):
        self.client = APIClient()
        self.staff = sample_user('user@pnsn.org')
        self.staff.is_staff = True
        self.client.force_authenticate(self.staff)
        self.org = Organization.objects.create(name="UW")

    def test_invite_success(self):
        url = reverse('invite:user-invite')
        invited_user = sample_user('invited@pnsn.org')
        payload = {'user': invited_user.id}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_invite_non_user(self):
        '''should throw 404 for user not found'''
        non_user_id = 999999
        url = reverse('invite:user-invite')
        payload = {'user': str(non_user_id)}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_active_user_fail(self):
        '''should throw error when inviting active user'''
        active_user = sample_user(
            'active@pnsn.org',
            'secret',
            self.org,
            is_active=True)
        url = reverse('invite:user-invite')
        payload = {'user': active_user.id}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # register tests
    def test_register_user_success(self):
        '''invited user should be able to register with
            password and valid token'''
        url = reverse('invite:user-register')
        invited_user = sample_user('register@pnsn.org')
        invite_token = InviteToken.objects.create(user=invited_user)
        token = base64.urlsafe_b64encode(
            str(invite_token.id).encode()).decode()
        payload = {'token': token, 'password': 'supersecret'}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_register_user_bad_token(self):
        '''bad token should fail'''
        url = reverse('invite:user-register')
        token = 'somebadtoken'
        payload = {'token': token, 'password': 'supersecret'}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_token(self):
        '''bad token should fail'''
        url = reverse('invite:user-register')
        invited_user = sample_user('register@pnsn.org')
        invite_token = InviteToken.objects.create(user=invited_user)
        expire_after = settings.INVITE_TOKEN_EXPIRY_TIME
        invite_token.created_at = \
            invite_token.created_at - timedelta(hours=expire_after + 1)
        invite_token.save()
        token = base64.urlsafe_b64encode(
            str(invite_token.id).encode()).decode()
        payload = {'token': token, 'password': 'supersecret'}
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
