from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from squac.test_mixins import sample_user
from core.models import Notification

'''
    to run this file only
    ./mg.sh "test user.tests.test_notification_permissions && flake8"
'''


class NotificationPermissionTests(TestCase):
    '''Test notification permissions'''

    def setUp(self):
        self.client = APIClient()
        self.me = sample_user('me@email.com')
        self.other = sample_user('other@email.com')
        self.admin = sample_user('admin@email.com')
        self.admin.is_staff = True
        self.admin.save()

        self.notification = Notification.objects.create(
            user=self.me
        )

    def test_me_can_get(self):
        '''Owner can see their notifications'''
        url = reverse(
            'user:notification-detail',
            kwargs={'pk': self.notification.id}
        )
        self.client.force_authenticate(self.me)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_get(self):
        '''Admin can see all notifications'''
        url = reverse(
            'user:notification-detail',
            kwargs={'pk': self.notification.id}
        )
        self.client.force_authenticate(self.admin)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_can_not_get(self):
        '''Owner can see their notifications'''
        url = reverse(
            'user:notification-detail',
            kwargs={'pk': self.notification.id}
        )
        self.client.force_authenticate(self.other)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
