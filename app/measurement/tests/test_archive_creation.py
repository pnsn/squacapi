from django.contrib.auth import get_user_model
from django.utils import timezone
from io import StringIO
from math import isnan, isfinite
import numpy as np
from django.core.management import call_command
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import random

from hypothesis import given
from hypothesis.strategies import (lists, datetimes, just, deferred, integers,
                                   data)
from hypothesis.extra.django import TestCase, from_model

from measurement.models import Metric, Measurement, ArchiveDay, ArchiveMonth
from nslc.models import Network, Channel
from squac.test_mixins import sample_user, round_to_decimals

# to run only this file
#   ./mg.sh "test measurement.tests.test_archive_creation && flake8"


class TestArchiveCreation(TestCase):
    """ Tests archive creation functionality """

    TEST_TIME = datetime(2019, 5, 5)
    DOUBLE_DECIMAL_PLACES = 6

    ARCHIVE_TYPE = {
        'day': ArchiveDay,
        'month': ArchiveMonth
    }

    def generate_measurements(self, day):
        """Generate measurements using Hypothesis"""
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

    def make_measurements(self, start_time, metric, n_metrics=10):
        """Generate measurements without using Hypothesis"""
        channel_id = Channel.objects.first()
        user_id = get_user_model().objects.first()
        measurements = []
        for i in range(n_metrics):
            tmp = Measurement.objects.create(
                metric=metric,
                channel=channel_id,
                value=random.randrange(-(10**8), 10**8),
                starttime=start_time,
                endtime=start_time + relativedelta(seconds=10 * i),
                user=user_id
            )
            measurements.append(tmp)
        return measurements

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
        self.metric2 = Metric.objects.create(
            name='Metric test 2',
            code='124',
            unit='meter',
            default_minval=2,
            default_maxval=12.0,
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
            sta='RCM',
            sta_name='Camp Muir',
            loc="--",
            net=self.net,
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
        yesterday = data.draw(self.generate_measurements(
            self.TEST_TIME - relativedelta(days=1)))
        today = data.draw(self.generate_measurements(
            self.TEST_TIME))

        # create archives of past 1 day
        out = StringIO()
        period_end = self.TEST_TIME + relativedelta(days=1)
        period_end = period_end.replace(tzinfo=pytz.UTC)
        call_command('archive_measurements', 'day',
                     period_end=period_end,
                     stdout=out)

        # check Archive was only created for today
        self.assertEqual(len(ArchiveDay.objects.all()),
                         1 if today else 0)

        # check the archives have the right statistics, if they exist
        if yesterday:
            self.check_queryset_was_not_archived(yesterday, 'day')
        if today:
            self.check_queryset_was_archived(today, 'day')

    @given(data())
    def test_multi_day_archive(self, data):
        """ make sure multiple days' stats are correctly summarized """

        # generate measurements for two days ago, yesterday and today
        two_days = data.draw(self.generate_measurements(
            self.TEST_TIME - relativedelta(days=2)))
        yesterday = data.draw(self.generate_measurements(
            self.TEST_TIME - relativedelta(days=1)))
        today = data.draw(self.generate_measurements(
            self.TEST_TIME))

        # create archives of past 2 days
        out = StringIO()
        period_start = self.TEST_TIME + relativedelta(days=0)
        period_start = period_start.replace(tzinfo=pytz.UTC)
        period_end = self.TEST_TIME + relativedelta(days=1)
        period_end = period_end.replace(tzinfo=pytz.UTC)
        call_command('backfill_archives', 'day', '--overwrite',
                     start_time=period_start,
                     end_time=period_end,
                     stdout=out)

        # check the correct number of archives were created
        self.assertEqual(len(ArchiveDay.objects.all()),
                         sum([1 if day else 0
                              for day in (yesterday, today)]))

        # check the archives have the right statistics, if they exist
        if two_days:
            self.check_queryset_was_not_archived(two_days, 'day')
        if yesterday:
            self.check_queryset_was_archived(yesterday, 'day')
        if today:
            self.check_queryset_was_archived(today, 'day')

    @given(data())
    def test_archive_redundant(self, data):
        """
        make sure when archive command is called multiple times for a given
        interval it will not create duplicate archives
        """
        test_time = datetime(2005, 6, 7)

        # generate measurements for a day
        day_data = data.draw(self.generate_measurements(test_time))

        # create archives for day
        out = StringIO()
        period_end = test_time + relativedelta(days=1)
        period_end = period_end.replace(tzinfo=pytz.UTC)
        call_command('archive_measurements', 'day',
                     period_end=period_end,
                     stdout=out)

        # get number of archives
        n_archives = ArchiveDay.objects.filter(
            starttime__gte=period_end - relativedelta(days=1)).filter(
            starttime__lt=period_end).count()

        # call archive again
        call_command('archive_measurements', 'day',
                     period_end=period_end,
                     stdout=out)

        # check that the number of archives didn't change
        n_archives2 = ArchiveDay.objects.filter(
            starttime__gte=period_end - relativedelta(days=1)).filter(
            starttime__lt=period_end).count()

        if day_data:
            self.assertTrue(n_archives > 0)
        self.assertEqual(n_archives, n_archives2)

    def test_archive_overwrite_feature(self):
        """test the --no-overwrite/--overwrite option for archiving"""
        def getArchiveId(starttime, endtime, metric):
            """Return id of matching archive, for easy testing"""
            archive = ArchiveDay.objects.filter(starttime__gte=starttime,
                                                endtime__lt=endtime,
                                                metric=metric)
            if archive:
                return archive.first().id
            else:
                return None

        test_time = datetime(2003, 4, 5, tzinfo=pytz.UTC)
        period_end = test_time + relativedelta(days=1)
        out = StringIO()

        # Create and archive measurements
        m1 = self.make_measurements(test_time, self.metric)
        call_command('archive_measurements', 'day',
                     period_end=period_end,
                     stdout=out)

        # Confirm measurements were archived and get archive id
        a1_1 = getArchiveId(test_time, period_end, self.metric)
        self.check_queryset_was_archived(m1, 'day')

        # Archive new measurements with --no-overwrite. Previous archives
        # should remain
        m2 = self.make_measurements(test_time, self.metric2)
        call_command('archive_measurements', 'day', '--no-overwrite',
                     period_end=period_end,
                     stdout=out)

        a1_2 = getArchiveId(test_time, period_end, self.metric)
        a2_2 = getArchiveId(test_time, period_end, self.metric2)
        self.check_queryset_was_archived(m1, 'day')
        self.check_queryset_was_archived(m2, 'day')
        self.assertEqual(a1_1, a1_2)

        # Now overwrite and see if ids change
        call_command('archive_measurements', 'day', '--overwrite',
                     period_end=period_end,
                     stdout=out)

        a1_3 = getArchiveId(test_time, period_end, self.metric)
        a2_3 = getArchiveId(test_time, period_end, self.metric2)
        self.check_queryset_was_archived(m1, 'day')
        self.check_queryset_was_archived(m2, 'day')
        self.assertNotEqual(a1_2, a1_3)
        self.assertNotEqual(a2_2, a2_3)

    @given(data())
    def test_month_archive(self, data):
        """ make sure month archive starts on the 1st and doesn't go into
        current month
        """
        test_time = datetime(2005, 6, 7)

        # generate measurements for a day
        this_month = data.draw(self.generate_measurements(
            test_time))
        last_month = data.draw(self.generate_measurements(
            test_time - relativedelta(months=1)))
        last_month_day1 = data.draw(self.generate_measurements(
            test_time - relativedelta(months=1, day=1)))
        last_month_end = data.draw(self.generate_measurements(
            test_time - relativedelta(months=1, day=28)))

        all_month = last_month + last_month_day1 + last_month_end

        # create month archive
        out = StringIO()
        period_end = test_time
        period_end = period_end.replace(tzinfo=pytz.UTC)
        call_command('archive_measurements', 'month',
                     period_end=period_end,
                     stdout=out)

        # check the correct number of archives were created
        self.assertEqual(len(ArchiveMonth.objects.all()),
                         1 if all_month else 0)

        # check the archives have the right statistics, if they exist
        if all_month:
            self.check_queryset_was_archived(all_month, 'month')
        if this_month:
            self.check_queryset_was_not_archived(this_month, 'month')

    def check_queryset_was_archived(self, measurements, archive_type):
        """ checks that the entire given queryset of measurements was
        successfully archived """
        test_metric = measurements[0].metric
        # refresh values from db for consistency with query
        measurement_data = [Measurement.objects.get(id=m.id).value for m in
                            measurements]
        min_start = min([m.starttime for m in measurements])
        max_end = max([measurement.endtime for measurement in measurements])
        archive = self.ARCHIVE_TYPE[archive_type].objects.get(
            endtime=max_end, starttime=min_start, metric=test_metric)
        # Assert created archive has correct statistics
        self.assertAlmostEqual(min(measurement_data), archive.min)
        self.assertAlmostEqual(max(measurement_data), archive.max)
        self.assertAlmostEqual(
            round_to_decimals(np.mean(measurement_data).item(),
                              self.DOUBLE_DECIMAL_PLACES),
            round_to_decimals(archive.mean,
                              self.DOUBLE_DECIMAL_PLACES))
        self.assertEqual(
            round_to_decimals(np.median(measurement_data).item(),
                              self.DOUBLE_DECIMAL_PLACES),
            round_to_decimals(archive.median,
                              self.DOUBLE_DECIMAL_PLACES))

        # python and sql calculate stdev differently, break down the cases
        if len(measurements) > 1 and all([isfinite(value)
                                         for value in measurement_data]):
            self.assertAlmostEqual(
                round_to_decimals(np.std(measurement_data, ddof=1).item(),
                                  self.DOUBLE_DECIMAL_PLACES),
                round_to_decimals(archive.stdev,
                                  self.DOUBLE_DECIMAL_PLACES))
        elif all([isfinite(value) for value in measurement_data]):
            self.assertAlmostEqual(0, archive.stdev)
        else:
            self.assertTrue(isnan(archive.stdev))
        self.assertEqual(len(measurements), archive.num_samps)
        self.assertEqual(min_start, archive.starttime)
        self.assertEqual(max_end, archive.endtime)

    def check_queryset_was_not_archived(self, measurements, archive_type):
        """ checks that the entire given queryset of measurements was
        not archived """
        test_metric = measurements[0].metric
        min_start = min([m.starttime for m in measurements])
        max_end = max([measurement.endtime for measurement in measurements])
        self.assertFalse(self.ARCHIVE_TYPE[archive_type].objects.filter(
            endtime=max_end, starttime=min_start, metric=test_metric).exists())
