from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from datetime import datetime
import pytz
from measurement.models import Metric, Measurement, Monitor
from nslc.models import Network, Channel, Group
from squac.test_mixins import sample_user, create_group
from organization.models import Organization


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
                        'view_archivemonth', 'add_archivemonth',
                        'view_monitor', 'add_monitor', 'change_monitor',
                        'delete_monitor',
                        'view_trigger', 'add_trigger', 'change_trigger',
                        'delete_trigger',
                        'view_alert', 'add_alert', 'change_alert',
                        'delete_alert',
                        'view_threshold', 'add_threshold', 'change_threshold',
                        'delete_threshold'
                        ]

VIEWER_PERMISSIONS = ['view_metric',
                      'view_measurement',
                      'view_archivehour',
                      'view_archiveday',
                      'view_archiveweek',
                      'view_archivemonth',
                      'view_threshold'
                      ]


class MeasurementPermissionTests(TestCase):
    '''Test authenticated reporter permissions'''

    def setUp(self):
        '''create sample authenticated user'''
        self.reporter = sample_user()
        self.reporter2 = sample_user('reporter2@pnsn.org')
        self.viewer = sample_user('viewer@pnsn.org')
        self.other = sample_user('other@pnsn.org')
        self.reporter_client = APIClient()
        self.reporter2_client = APIClient()
        self.viewer_client = APIClient()

        self.reporter_group = create_group('reporter', REPORTER_PERMISSIONS)
        self.viewer_group = create_group('viewer', VIEWER_PERMISSIONS)
        self.reporter.groups.add(self.reporter_group)
        self.reporter2.groups.add(self.reporter_group)
        self.viewer.groups.add(self.viewer_group)
        self.reporter_client.force_authenticate(user=self.reporter)
        self.reporter2_client.force_authenticate(user=self.reporter)
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

        self.organization = Organization.objects.create(
            name='PNSN'
        )
        self.grp = Group.objects.create(
            name='Test group',
            share_all=False,
            share_org=False,
            user=self.reporter,
            organization=self.organization
        )

        self.grp.channels.add(self.chan)

        # reporter 1
        self.monitor = Monitor.objects.create(
            metric=self.metric,
            channel_group=self.grp,
            interval_type='hour',
            interval_count=1,
            num_channels=1,
            stat="sum",
            name='test',
            user=self.reporter
        )
        # and one for reporter 2
        self.monitor2 = Monitor.objects.create(
            metric=self.metric,
            channel_group=self.grp,
            interval_type='hour',
            interval_count=1,
            num_channels=1,
            stat="sum",
            name='test',
            user=self.reporter2
        )

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
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_monitor'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_monitor'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.change_monitor'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.delete_monitor'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_trigger'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_trigger'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.change_trigger'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.delete_trigger'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_alert'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_alert'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.change_alert'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.delete_alert'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.view_threshold'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.add_threshold'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.change_threshold'))
        self.assertTrue(self.reporter.has_perm(
            'measurement.delete_threshold'))

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
        self.assertFalse(self.viewer.has_perm(
            'measurement.view_monitor'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_monitor'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_monitor'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_monitor'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.view_trigger'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_trigger'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_trigger'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_trigger'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.view_alert'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_alert'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_alert'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_alert'))
        self.assertTrue(self.viewer.has_perm(
            'measurement.view_threshold'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.add_threshold'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.change_threshold'))
        self.assertFalse(self.viewer.has_perm(
            'measurement.delete_threshold'))

    def test_get_list_monitors(self):
        self.assertFalse(self.reporter.is_staff)
        url = reverse('measurement:monitor-list')
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_get_user_monitor(self):
        url = reverse('measurement:monitor-detail',
                      kwargs={'pk': self.monitor.id})
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_other_user_monitor(self):
        url = reverse('measurement:monitor-detail',
                      kwargs={'pk': self.monitor2.id})
        res = self.reporter_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
