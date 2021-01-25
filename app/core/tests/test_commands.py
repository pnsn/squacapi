import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.utils import OperationalError
from django.db import NotSupportedError
from django.test import TestCase
from io import StringIO

from organization.models import Organization

'''
./mg.sh "test core.tests.test_commands && flake8"
'''


class CommandTests(TestCase):

    def test_wait_for_db_ready(self):
        '''Test waiting for db when db is avialable'''
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.return_value = True
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 1)

    @patch('time.sleep', return_value=True)
    def test_wait_for_db(self, ts):
        '''test waiting for db'''
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.side_effect = [OperationalError] * 5 + [True]
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 6)

    def test_createsuperuser(self):
        '''Test creating a new super user from command'''
        default_org = Organization.objects.create(name='PNSN')
        out = StringIO()
        call_command('createsuperuser', email='test@email.com', stdout=out,
                     interactive=False)
        self.assertEqual(out.getvalue(), 'Superuser created successfully.\n')
        new_superuser = get_user_model().objects.get(email='test@email.com')
        self.assertIsNotNone(new_superuser)
        self.assertEqual(new_superuser.organization, default_org)

    def test_bootstrap_db_fails_on_invalid_db(self):
        os.environ.setdefault("SQUAC_DB_NAME", "not_real_db")
        with self.assertRaises(NotSupportedError):
            call_command('bootstrap_db', days=7)
