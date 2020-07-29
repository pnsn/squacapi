from django.test import TestCase
from django.contrib.auth import get_user_model
from organization.models import Organization
from squac.test_mixins import sample_user, create_group


# to run only the app tests:
#     /mg.sh "test core && flake8"
# to run only this file
#     ./mg.sh "test core.tests.test_models  && flake8"


class ModelTests(TestCase):

    def setUp(self):
        self.organization = Organization.objects.create(name="PNSN")
        self.viewer = create_group("viewer", [])
        self.reporter = create_group("reporter", [])
        self.contributor = create_group("contributor", [])
        self.org_admin = create_group("org_admin", [])
        self.user = sample_user('user@pnsn.org')

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

    def test_new_user_email_normalized(self):
        '''Test email for new user is lowercased'''
        email = "test@pNsn.org"
        user = get_user_model().objects.create_user(
            email,
            "12323",
            self.organization
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        '''test createing user with no email reaises error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                None,
                '1243',
                self.organization
            )

    def test_new_user_no_organization(self):
        '''test createing user with no email reaises error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                None,
                '1243'
            )

    def test_create_new_superuser(self):
        '''Test creating new superuser'''
        user = get_user_model().objects.create_superuser(
            'test@pnsn.org',
            'adjfkjds',
            self.organization
        )
        self.assertTrue(user.is_superuser)

    def test_belongs_to_group(self):
        '''test the belongs to group method'''
        self.user.groups.add(self.viewer)
        self.assertTrue(self.user.belongs_to_group(self.viewer.name))
        self.assertFalse(self.user.belongs_to_group(self.reporter.name))
        '''a group that doesn't exist '''
        self.assertFalse(self.user.belongs_to_group("something"))

    def test_adding_duplicate_group(self):
        self.user.groups.add(self.viewer)
        self.user.groups.add(self.viewer)

    def test_set_permission_groups(self):
        user = sample_user("user2@pnsn.org")
        user.set_permission_groups([self.reporter])
        self.assertTrue(len(user.groups.all()) == 2)
        user.set_permission_groups([self.viewer])
        self.assertTrue(len(user.groups.all()) == 1)
        user.set_permission_groups([self.contributor, self.viewer])
        self.assertTrue(len(user.groups.all()) == 3)
