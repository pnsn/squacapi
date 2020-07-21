from django.test import TestCase
from django.contrib.auth import get_user_model
from organization.models import Organization


class ModelTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(name="PNSN")

    def test_create_user_with_email_successful(self):
        '''test creating a new user with an email success'''
        email = 'test@uw.edu'
        password = 'supersecret'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            organization=self.organization
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    # def test_new_user_email_normalized(self):
    #     '''Test email for new user is lowercased'''
    #     email = "test@pNsn.org"
    #     user = get_user_model().objects.create_user(
    #         email,
    #         "12323",
    #         self.organization
    #     )

    #     self.assertEqual(user.email, email.lower())

    # def test_new_user_invalid_email(self):
    #     '''test createing user with no email reaises error'''
    #     with self.assertRaises(ValueError):
    #         get_user_model().objects.create_user(
    #             None,
    #             '1243',
    #             self.organization
    #         )

    # def test_new_user_no_organization(self):
    #     '''test createing user with no email reaises error'''
    #     with self.assertRaises(ValueError):
    #         get_user_model().objects.create_user(
    #             None,
    #             '1243'
    #         )

    # def test_create_new_superuser(self):
    #     '''Test creating new superuser'''
    #     user = get_user_model().objects.create_superuser(
    #         'test@pnsn.org',
    #         'adjfkjds',
    #         self.organization
    #     )
    #     self.assertTrue(user.is_superuser)
