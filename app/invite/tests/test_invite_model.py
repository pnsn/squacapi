from django.test import TestCase
from unittest.mock import patch
from invite.models import InviteToken
from squac.test_mixins import sample_user


'''
 To run these tests
 ./mg.sh "test invite.tests.test_invite_model && flake8"
'''


class InvitationAPITests(TestCase):
    '''For authenticated tests in dashboard API'''

    def setUp(self):
        self.user = sample_user('user@pnsn.org')

    @patch.object(InviteToken, 'send_invite')
    def test_token_creation(self, mock):
        token = InviteToken.objects.create(user=self.user)
        self.assertFalse(token.id is None)
        self.assertTrue(mock.called)
