from django.contrib.auth import get_user_model
from django.utils import timezone
from io import StringIO
from math import isnan, isfinite, floor, log10
import numpy as np
from django.core.management import call_command
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

from hypothesis import given
from hypothesis.strategies import (lists, datetimes, just, deferred, integers,
                                   data)
from hypothesis.extra.django import TestCase, from_model

from measurement.models import Metric, Measurement, ArchiveDay
from nslc.models import Network, Channel
from squac.test_mixins import sample_user

# to run only this file
#   ./mg.sh "test measurement.tests.test_archive_creation && flake8"


class TestArchiveCreation(TestCase):
    """ Tests archive creation functionality """

    TEST_TIME = datetime(2019, 5, 5)
    DOUBLE_DECIMAL_PLACES = 6

    def generate_measurements(day):
        return lists(from_model(Measurement,
                                # deferred so that select happens only after
                                # they are guaranteed to exist (created in
                                # setUp)
                                metric=deferred(
                                    lambda: just(Metric.objects.first())),
                                channel=deferred(
                                    lambda: just(Channel.objects.first())),
                                user=deferred(
                                    lambda: just(get_user_model().objects\
                                                                 .first())
                                ),
                                value=integers(
                                    min_value=-(10**16) + 1,
                                    max_value=(10**16) - 1),
                                # constrain end times to be in range
                                starttime=datetimes(
                                    min_value=day + relativedelta(seconds=1),
                                    max_value=day + relativedelta(hours=23),
                                    timezones=just(pytz.UTC))))

    def setUp(self):
        timezone.now()
        self.user = sample_user()
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

    def tearDown(self):
        self.user.delete()

    @given(data())
    def test_single_day_archive(self, data):
        """ make sure a a single day's stats are correctly summarized """
        # generate measurements for yesterday and today
        yesterday = data.draw(TestArchiveCreation.generate_measurements(
            TestArchiveCreation.TEST_TIME - relativedelta(days=1)))
        today = data.draw(TestArchiveCreation.generate_measurements(
            TestArchiveCreation.TEST_TIME))

        # create archives of past 1 day
        out = StringIO()
        period_end = TestArchiveCreation.TEST_TIME + relativedelta(days=1)
        call_command('archive_measurements', 1, 'day',
                     period_end=period_end,
                     stdout=out)

        # check Archive was only created for today
        self.assertEqual(len(ArchiveDay.objects.all()),
                         1 if today else 0)

        # check the archives have the right statistics, if they exist
        if yesterday:
            self.check_queryset_was_not_archived(yesterday)
        if today:
            self.check_queryset_was_archived(today)

    @given(data())
    def test_multi_day_archive(self, data):
        """ make sure multiple days' stats are correctly summarized """

        # generate measurements for two days ago, yesterday and today
        two_days = data.draw(TestArchiveCreation.generate_measurements(
            TestArchiveCreation.TEST_TIME - relativedelta(days=2)))
        yesterday = data.draw(TestArchiveCreation.generate_measurements(
            TestArchiveCreation.TEST_TIME - relativedelta(days=1)))
        today = data.draw(TestArchiveCreation.generate_measurements(
            TestArchiveCreation.TEST_TIME))

        # create archives of past 2 days
        out = StringIO()
        period_end = TestArchiveCreation.TEST_TIME + relativedelta(days=1)
        call_command('archive_measurements', 2, 'day',
                     period_end=period_end,
                     stdout=out)

        # check the correct number of archives were created
        self.assertEqual(len(ArchiveDay.objects.all()),
                         sum([1 if day else 0
                              for day in (yesterday, today)]))

        # check the archives have the right statistics, if they exist
        if two_days:
            self.check_queryset_was_not_archived(two_days)
        if yesterday:
            self.check_queryset_was_archived(yesterday)
        if today:
            self.check_queryset_was_archived(today)

    def check_queryset_was_archived(self, measurements):
        """ checks that the entire given queryset of measurements was
        successfully archived """
        # refresh values from db for consistency with query
        measurement_data = [Measurement.objects.get(id=m.id).value for m in
                            measurements]
        min_start = min([m.starttime for m in measurements])
        max_end = max([measurement.endtime for measurement in measurements])
        archive = ArchiveDay.objects.get(endtime=max_end, starttime=min_start)
        # Assert created archive has correct statistics
        self.assertAlmostEqual(min(measurement_data), archive.min)
        self.assertAlmostEqual(max(measurement_data), archive.max)
        self.assertAlmostEqual(
            self.round_to_decimals(np.mean(measurement_data).item(),
                                   self.DOUBLE_DECIMAL_PLACES),
            self.round_to_decimals(archive.mean,
                                   self.DOUBLE_DECIMAL_PLACES))
        self.assertEqual(
            self.round_to_decimals(np.median(measurement_data).item(),
                                   self.DOUBLE_DECIMAL_PLACES),
            self.round_to_decimals(archive.median,
                                   self.DOUBLE_DECIMAL_PLACES))

        # python and sql calculate stdev differently, break down the cases
        if len(measurements) > 1 and all([isfinite(value)
                                         for value in measurement_data]):
            self.assertAlmostEqual(
                self.round_to_decimals(np.std(measurement_data, ddof=1).item(),
                                       self.DOUBLE_DECIMAL_PLACES),
                self.round_to_decimals(archive.stdev,
                                       self.DOUBLE_DECIMAL_PLACES))
        elif all([isfinite(value) for value in measurement_data]):
            self.assertAlmostEqual(0, archive.stdev)
        else:
            self.assertTrue(isnan(archive.stdev))

        self.assertEqual(len(measurements), archive.num_samps)
        self.assertEqual(min_start, archive.starttime)
        self.assertEqual(max_end, archive.endtime)

    def check_queryset_was_not_archived(self, measurements):
        """ checks that the entire given queryset of measurements was
        not archived """
        min_start = min([m.starttime for m in measurements])
        max_end = max([measurement.endtime for measurement in measurements])
        self.assertFalse(ArchiveDay.objects
                                   .filter(endtime=max_end,
                                           starttime=min_start)
                                   .exists())

    def round_to_decimals(self, n, places):
        """
        returns `n` rounded to `places` total decimal digits
        (fractional and whole)
        """
        try:
            digits = floor(log10(abs(n))) + 1
            rounded = round(n, places - digits)
            return rounded
        except (OverflowError, ValueError):
            return n
