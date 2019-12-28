from django.contrib.auth import get_user_model
from django.utils import timezone
from io import StringIO
from statistics import median, mean, stdev
from django.core.management import call_command
from datetime import datetime
from dateutil import relativedelta
import pytz

from hypothesis import given, assume
from hypothesis.strategies import lists, datetimes, just, deferred
from hypothesis.extra.django import TestCase, from_model
from hypothesis.extra.dateutil import timezones

from measurement.models import Metric, Measurement, Archive
from nslc.models import Network, Channel


class TestArchiveCreation(TestCase):
    """ Tests archive creation functionality """

    TEST_TIME = datetime(2019, 5, 5, 8, 8, 7, 127325)

    def sample_user(email='test@pnsn.org', password="secret"):
        '''create a sample user for testing'''
        return get_user_model().objects.create_user(email, password)

    def setUp(self):
        timezone.now()
        self.user = TestArchiveCreation.sample_user()
        self.metric = Metric.objects.create(
            name='Metric test',
            code='123',
            unit='meter',
            default_minval=1,
            default_maxval=10.0,
            user=self.user
        )
        self.net = Network.objects.create(
            code="UW",
            name="University of Washington",
            user=self.user
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
            user=self.user,
            starttime=datetime(1970, 1, 1, tzinfo=pytz.UTC),
            endtime=datetime(2599, 12, 31, tzinfo=pytz.UTC)
        )

    # generate list of measurements for single day
    @given(lists(from_model(Measurement,
                            # deferred so that select happens only after they
                            # are guaranteed to exist (created in setUp)
                            metric=deferred(
                                lambda: just(Metric.objects.first())),
                            channel=deferred(
                                lambda: just(Channel.objects.first())),
                            user=deferred(
                                lambda: just(get_user_model().objects.first())
                                ),
                            # constrain dates to be in range
                            starttime=datetimes(
                                min_value=TEST_TIME-relativedelta(hours=23),
                                max_value=TEST_TIME,
                                timezones=timezones()),
                            endtime=datetimes(
                                min_value=TEST_TIME-relativedelta(hours=23),
                                max_value=TEST_TIME,
                                timezones=timezones()))))
    def test_single_day_archive(self, measurements):
        """ make sure a a single day's stats are correctly summarized """
        assume(len(measurements) > 0)

        out = StringIO()
        call_command('archive_measurements', 1, 'day',
                     period_end=TestArchiveCreation.TEST_TIME, stdout=out)
        archive = Archive.objects.first()

        measurement_data = [measurement.value for measurement in
                            Measurement.objects.all()]
        min_start = min([m.starttime for m in measurements])
        max_end = max([measurement.endtime for measurement in measurements])

        self.assertEqual(Archive.DAY, archive.archive_type)
        self.assertAlmostEqual(min(measurement_data), archive.min)
        self.assertAlmostEqual(max(measurement_data), archive.max)
        self.assertAlmostEqual(mean(measurement_data), archive.mean)
        self.assertAlmostEqual(median(measurement_data), archive.median)
        self.assertAlmostEqual(
            stdev(measurement_data) if len(measurements) > 1 else 0,
            archive.stdev)
        self.assertEqual(len(measurements), archive.n)
        self.assertEqual(min_start, archive.starttime)
        self.assertEqual(max_end, archive.endtime)
