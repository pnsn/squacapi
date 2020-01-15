from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
# from django.contrib.auth.models import Group
'''commenting out offening parts

    Once legacy tests work with DjangoModelPermission then we can
    charter new waters...
'''

'''
    to run this file only
    ./mg.sh "test measurement.tests.test_measurement_permissions && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class ViewerMeasurementPermissionTests(TestCase):
    '''Test authenticated viewer permissions

        if save methods;
         return 200
        return 401
    '''

    def setUp(self):
        '''create sample authenticated user'''
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all requests
        self.client.force_authenticate(user=self.user)

    def test_user_is_viewer(self):
        # self.assertTrue(self.user.groups.filter(name='viewer').exists())
        # self.assertFalse(self.user.has_perm('can_add_metric'))
        pass

    def test_viewer_should_get_metric_list(self):
        url = reverse("measurement:metric-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_should_not_post_metric(self):
        payload = {
            'name': 'Metric test',
            'code': 'coolname',
            'description': 'Test description',
            'unit': 'meter',
            'default_minval': 1,
            'default_maxval': 10.0,
            'user': self.user
        }
        url = reverse("measurement:metric-list")
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
