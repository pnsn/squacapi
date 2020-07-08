from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime
import pytz
from measurement.models import Metric, Measurement
from nslc.models import Network, Channel

'''
    to run this file only
    ./mg.sh "test measurement.tests.test_measurement_permissions && flake8"

'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


'''permissons follow form

    view_model
    add_model
    change_model
    delete_model
'''


def create_group(name, permissions):
    '''takes name of group and list of permissions'''
    group = Group.objects.create(name=name)
    for p in permissions:
        perm = Permission.objects.get(codename=p)
        group.permissions.add(perm)
    return group


REPORTER_PERMISSIONS = ['view_metric', 'add_metric', 'change_metric',
                        'delete_metric',
                        'view_measurement', 'add_measurement',
                        'change_measurement', 'delete_measurement',
                        'view_archive', 'add_archive']

VIEWER_PERMISSIONS = ['view_metric',
                      'view_measurement',
                      'view_archive']


class MeasurementPermissionTests(TestCase):
    '''Test authenticated reporter permissions'''

    def setUp(self):
        '''create sample authenticated user'''
        self.reporter = sample_user()
        self.viewer = sample_user('viewer@pnsn.org')
        self.other = sample_user('other@pnsn.org')
        self.reporter_client = APIClient()
        self.viewer_client = APIClient()

        self.reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.reporter.groups.add(self.reporter_group)
        self.viewer.groups.add(self.viewer_group)
        self.reporter_client.force_authenticate(user=self.reporter)
        self.viewer_client.force_authenticate(user=self.viewer)

        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            code="someotherfuknthing",
            default_minval=1,
            default_maxval=10.0,
            user=self.reporter,
            reference_url='pnsn.org'
        )
        self.metric_other = Metric.objects.create(
            name='Sample metric1',
            unit='furlong',
            code="someotherfuknthingajig",
            default_minval=1,
            default_maxval=10.0,
            user=self.other,
            reference_url='pnsn.org'
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.reporter
        )
        self.chan = Channel.objects.create(
            code='EHZ',
            name="EHZ",
            station_code='RCM',
            station_name='Camp Muir',
            loc="--",
            network=self.net,
            lat=45,
            lon=-122,
            elev=0,
            user=self.reporter,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )
        self.measurement = Measurement.objects.create(
            metric=self.metric,
            channel=self.chan,
            value=3.0,
            starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 5, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            user=self.reporter
        )
        self.measurement_other = Measurement.objects.create(
            metric=self.metric,
            channel=self.chan,
            value=4.0,
            starttime=datetime(2019, 6, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            endtime=datetime(2019, 6, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            user=self.other
        )
        # self.archive = Archive.objects.create(
        #     archive_type=Archive.DAY,
        #     channel=self.chan,
        #     metric=self.metric,
        #     min=0, max=0, mean=0, median=0, stdev=0, num_samps=1,
        #     starttime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
        #     endtime=datetime(2019, 5, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC)
        # )

    def test_reporter_has_perms(self):
        '''reporters can:

            *all actions on metrics
            *view/add on measurements and archives
        '''
        self.assertTrue(self.reporter.has_perm('measurement.view_metric'))
        self.assertTrue(self.reporter.has_perm('measurement.add_metric'))
        self.assertTrue(self.reporter.has_perm('measurement.change_metric'))
        self.assertTrue(self.reporter.has_perm('measurement.delete_metric'))
        self.assertTrue(self.reporter.has_perm('measurement.view_measurement'))
        self.assertTrue(self.reporter.has_perm('measurement.add_measurement'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.change_measurement'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.delete_measurement'))
        self.assertTrue(self.reporter.has_perm('measurement.view_archive'))
        self.assertTrue(self.reporter.has_perm('measurement.add_archive'))
        self.assertFalse(self.reporter.has_perm('measurement.change_archive'))
        self.assertFalse(self.reporter.has_perm('measurement.delete_archive'))

    def test_viewer_has_perms(self):
        '''viewers can view all models'''
        self.assertTrue(self.viewer.has_perm('measurement.view_metric'))
        self.assertFalse(self.viewer.has_perm('measurement.add_metric'))
        self.assertFalse(self.viewer.has_perm('measurement.change_metric'))
        self.assertFalse(self.viewer.has_perm('measurement.delete_metric'))
        self.assertTrue(self.viewer.has_perm('measurement.view_measurement'))
        self.assertFalse(self.viewer.has_perm('measurement.add_measurement'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_measurement'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_measurement'))
        self.assertTrue(self.viewer.has_perm('measurement.view_archive'))
        self.assertFalse(self.viewer.has_perm('measurement.add_archive'))
        self.assertFalse(self.viewer.has_perm('measurement.change_archive'))
        self.assertFalse(self.viewer.has_perm('measurement.delete_archive'))

    # #### metric tests ####
    def test_viewer_reporter_view_metric(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_create_metric(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Metric test',
            'code': 'coolname',
            'description': 'Test description',
            'unit': 'meter',
            'default_minval': 1,
            'default_maxval': 10.0,
            'reference_url': 'pnsn.org'
        }
        # viewer
        res = self.viewer_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # reporter
        res = self.reporter_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_reporter_delete_metric(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        res = self.viewer_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_reporter_cannot_delete_other_metric(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric_other.id}
        )
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ## measurement tests ###
    def test_viewer_reporter_view_measurement(self):
        url = reverse(
            'measurement:measurement-detail',
            kwargs={'pk': self.measurement.id}
        )
        # viewer
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reporter
        res = self.viewer_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_viewer_reporter_create_measurement(self):
        url = reverse('measurement:measurement-list')
        payload = {
            'metric': self.metric.id,
            'channel': self.chan.id,
            'value': 47.0,
            'starttime': datetime(
                2019, 4, 5, 8, 8, 7, 127325, tzinfo=pytz.UTC),
            'endtime': datetime(2019, 4, 5, 9, 8, 7, 127325, tzinfo=pytz.UTC),
            'user': self.viewer
        }
        # viewer
        res = self.viewer_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # reporter
        payload['user'] = self.reporter
        res = self.reporter_client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_viewer_reporter_delete_measurement(self):
        url = reverse(
            'measurement:measurement-detail',
            kwargs={'pk': self.measurement.id}
        )
        res = self.viewer_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_reporter_cannot_delete_other_measurement(self):
        url = reverse(
            'measurement:measurement-detail',
            kwargs={'pk': self.measurement_other.id}
        )
        res = self.reporter_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
