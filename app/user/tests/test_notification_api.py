from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Contact, Notification
from squac.test_mixins import sample_user


'''Tests for all Notification model API

to run only the app tests:
    /mg.sh "test user && flake8"
to run only this file
    ./mg.sh "test user.tests.test_notification_api && flake8"
'''


class UnAuthenticatedNotificationApiTests(TestCase):
    '''Test the nslc api (public). should 401 on all requests'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate user
        self.client.force_authenticate(user=None)
        self.contact = Contact.objects.create(
            user=self.user,
            sms_value='1'
        )
        # self.notification = Notification.objects.create(
        #     user=self.user,
        #     notification_type=Notification.NotificationType.SMS,
        #     contact=self.contact
        # )
        self.notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.SMS,
            value='1'
        )

    def test_notification_unathorized(self):
        '''test if unauth user can read or write to notification'''
        url = reverse(
            'user:notification-detail', kwargs={'pk': self.notification.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user:notification-list')
        payload = {}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateNotificationAPITests(TestCase):
    '''all authenticated tests go here'''

    def setUp(self):
        self.client = APIClient()
        self.admin = sample_user(email="test@pnsn.org", password="secret")
        self.admin.is_staff = True
        self.admin.save()
        self.other = sample_user(email="other@pnsn.org", password="secret")
        self.client.force_authenticate(self.admin)
        self.contact_admin = Contact.objects.create(
            user=self.admin,
            sms_value='1'
        )
        self.contact_other = Contact.objects.create(
            user=self.other,
            email_value=self.other.email
        )
        # self.notification = Notification.objects.create(
        #     user=self.admin,
        #     notification_type=Notification.NotificationType.SMS,
        #     contact=self.contact_admin
        # )
        # self.other_notification = Notification.objects.create(
        #     user=self.other,
        #     notification_type=Notification.NotificationType.SMS,
        #     contact=self.contact_other
        # )
        self.notification = Notification.objects.create(
            user=self.admin,
            notification_type=Notification.NotificationType.SMS,
            value='1'
        )
        self.other_notification = Notification.objects.create(
            user=self.other,
            notification_type=Notification.NotificationType.SMS,
            value=self.other.email
        )

    def test_get_notification(self):
        '''test if str is corrected'''
        url = reverse(
            'user:notification-detail', kwargs={'pk': self.notification.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_notification(self):
        url = reverse('user:notification-list')
        payload = {'notification_type': Notification.NotificationType.EMAIL,
                   'user': self.other,
                   'value': 'testemail'
                   }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(id=res.data['id'])
        self.assertEqual(
            payload['notification_type'],
            notification.notification_type
        )

    def test_admin_can_view_all_notifications(self):
        url = reverse('user:notification-list')
        res = self.client.get(url)
        self.assertEqual(len(res.data), 2)

    def test_notifications_limited_to_owner(self):
        self.client.force_authenticate(self.other)
        url = reverse('user:notification-list')
        res = self.client.get(url)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(
            res.data[0]['user_id'],
            self.other.id
        )

    def test_create_contact(self):
        url = reverse('user:contact-list')
        payload = {
            'email_value': self.admin.email,
            'user': self.admin
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        contact = Contact.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(contact, key))

    def test_create_contact_bad_email(self):
        url = reverse('user:contact-list')
        payload = {
            'email_value': 'bademail',
            'user': self.admin
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contact_bad_email_wo_http(self):
        with self.assertRaises(ValidationError):
            contact = Contact.objects.create(
                user=self.other,
                email_value='bademail'
            )

    def test_create_contact_empty_email_no_error(self):
        contact = Contact.objects.create(
            user=self.other,
            email_value=''
        )
        self.assertEqual(contact.email_value, '')

    # def test_create_notification_empty_email(self):
    #     url = reverse('user:notification-list')
    #     payload = {'notification_type': Notification.NotificationType.EMAIL,
    #                'user': self.admin,
    #                'contact': self.contact_admin
    #                }
    #     res = self.client.post(url, payload)
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #     notification = Notification.objects.get(id=res.data['id'])
    #     self.assertEqual(
    #         payload['notification_type'],
    #         notification.notification_type
    #     )

    # def test_create_notification_bad_email(self):
    #     url = reverse('user:notification-list')
    #     payload = {'notification_type': Notification.NotificationType.EMAIL,
    #                'user': self.other,
    #                'contact': Contact.objects.create(
    #                     user=self.other,
    #                     email_value='1'
    #                 )
    #                }
    #     res = self.client.post(url, payload)
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_create_notification_bad_email_wo_http(self):
    #     # with self.assertRaises(ValidationError):
    #     notification = Notification.objects.create(
    #         notification_type=Notification.NotificationType.EMAIL,
    #         user=self.other,
    #         contact=Contact.objects.create(
    #             user=self.other,
    #             email_value='tempemail'
    #         )
    #     )
    #     print(f"\nlevel = {notification.level}"
    #           f"\ncontact = {notification.contact.email_value}"
    #           )



