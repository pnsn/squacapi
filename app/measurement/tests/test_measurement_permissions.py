from django.test import TestCase
from rest_framework.test import APIClient
from datetime import datetime
import pytz
from measurement.models import Metric, Measurement
from nslc.models import Network, Channel
from squac.test_mixins import sample_user, create_group


'''
    to run this file only
    ./mg.sh "test measurement.tests.test_measurement_permissions && flake8"

'''


'''permissons follow form

    view_model
    add_model
    change_model
    delete_model
'''

REPORTER_PERMISSIONS = ['view_metric', 'add_metric', 'change_metric',
                        'delete_metric',
                        'view_measurement', 'add_measurement',
                        'change_measurement', 'delete_measurement',
                        'view_archivehour', 'add_archivehour',
                        'view_archiveday', 'add_archiveday',
                        'view_archiveweek', 'add_archiveweek',
                        'view_archivemonth', 'add_archivemonth']

VIEWER_PERMISSIONS = ['view_metric',
                      'view_measurement',
                      'view_archivehour',
                      'view_archiveday',
                      'view_archiveweek',
                      'view_archivemonth']


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
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_archivehour'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_archivehour'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.change_archivehour'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.delete_archivehour'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_archiveday'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_archiveday'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.change_archiveday'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.delete_archiveday'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_archiveweek'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_archiveweek'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.change_archiveweek'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.delete_archiveweek'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_archivemonth'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_archivemonth'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.change_archivemonth'))
        self.assertFalse(self.reporter.has_perm(
            'measurement.delete_archivemonth'))

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
        self.assertTrue(self.viewer.has_perm(
            'measurement.view_archivehour'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_archivehour'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_archivehour'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_archivehour'))
        self.assertTrue(self.viewer.has_perm(
            'measurement.view_archiveday'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_archiveday'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_archiveday'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_archiveday'))
        self.assertTrue(self.viewer.has_perm(
            'measurement.view_archiveweek'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_archiveweek'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_archiveweek'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_archiveweek'))
        self.assertTrue(self.viewer.has_perm(
            'measurement.view_archivemonth'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_archivemonth'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_archivemonth'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_archivemonth'))
