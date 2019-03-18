from django.test import TestCase


class CalcTests(TestCase):
    '''simple tests to configure circleci'''

    def test_duhhh(self):
        '''now does 3==3'''
        self.assertEqual(3, 3)

    def test_derr(self):
        '''is true true?'''
        self.assertTrue(True)
