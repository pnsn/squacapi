from django.core.management.base import BaseCommand
from django.db.models import (Avg, StdDev, Min, Max, Count, F, FloatField,
                              CharField, Value as V)
from django.db.models.functions import (TruncDay, TruncMonth, TruncWeek,
                                        Coalesce, Concat)
from measurement.models import (Measurement, ArchiveDay, ArchiveMonth,
                                ArchiveWeek)
from measurement.aggregates.percentile import Percentile
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO
import pytz


class Command(BaseCommand):
    """ Command for creating archive entries"""

    help = 'Archives Measurements for the given time period'

    TIME_TRUNCATOR = {
        'day': TruncDay,
        'week': TruncWeek,
        'month': TruncMonth,
    }
    """" Django datetime extractors for dealing with portions of datetimes """

    DURATIONS = {
        'day': lambda count: relativedelta(days=count),
        'week': lambda count: relativedelta(weeks=count),
        'month': lambda count: relativedelta(months=count),
    }
    """ functions for generating timesteps of sizes """

    ARCHIVE_TYPE = {
        'day': ArchiveDay,
        'week': ArchiveWeek,
        'month': ArchiveMonth
    }
    """ Types of archive """

    def add_arguments(self, parser):
        parser.add_argument('archive_type',
                            choices=['day', 'week', 'month'],
                            help=('The granularity of the desired archive '
                                  '(i.e. day, week, month, etc.)'))
        parser.add_argument('--period_end',
                            type=lambda s: pytz.utc.localize(
                                datetime.strptime(s, "%m-%d-%Y")),
                            nargs='?',
                            default=datetime.now(tz=pytz.utc).replace(
                                hour=0, minute=0, second=0, microsecond=0),
                            help=('The end of the archiving period, '
                                  'non-inclusive (format: mm-dd-yyyy)'))
        parser.add_argument('--metric', action='append',
                            help='id of the metric to be archived',
                            default=[])
        parser.add_argument('--no-overwrite', dest='overwrite',
                            action='store_false')
        parser.add_argument('--overwrite', dest='overwrite',
                            action='store_true')

    def handle(self, *args, **kwargs):
        # extract args
        archive_type = kwargs['archive_type']
        metrics = kwargs['metric']
        overwrite = kwargs['overwrite']
        period_end = kwargs['period_end']
        # in order to make archives for longer periods use backfill_archives,
        # which calls this command
        period_size = 1
        period_start = period_end - self.DURATIONS[archive_type](period_size)

        if archive_type == 'month':
            # if archive_type is month, adjust period start/end to go from 1st
            # day of the month
            period_end = period_end.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            period_start = period_start.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
        elif archive_type == 'week':
            # if archive_type is week, adjust period start/end to go from
            # Monday of the given week
            period_end += relativedelta(hour=0, minute=0, second=0,
                                        microsecond=0, weekday=MO(-1))
            period_start += relativedelta(hour=0, minute=0, second=0,
                                          microsecond=0, weekday=MO(-1))

        # filter measurements down to time range
        measurements = Measurement.objects.filter(
            starttime__gte=period_start, starttime__lt=period_end)

        # if specific metrics were selected, filter for them
        if len(metrics) != 0:
            measurements = measurements.filter(metric__id__in=metrics)

        # get archives for same time period, to compare with measurements
        archives = self.ARCHIVE_TYPE[archive_type].objects.filter(
            starttime__gte=period_start, starttime__lt=period_end)

        # if overwriting archives, designate old ones to delete. Otherwise,
        # check to make sure we are only writing new ones
        if overwrite:
            n_archives_to_ignore = 0
            archives_to_delete = archives
            if len(metrics) != 0:
                archives_to_delete = archives_to_delete.filter(
                    metric_id__in=metrics)
        else:
            # exclude measurements that already have archives. This only works
            # correctly for a single time period
            archive_key = archives.annotate(
                m_c=Concat('metric_id',
                           V(' '),
                           'channel_id',
                           output_field=CharField())).values('m_c')
            measurements = measurements.annotate(
                m_c=Concat('metric_id',
                           V(' '),
                           'channel_id',
                           output_field=CharField())).exclude(
                m_c__in=archive_key)
            # make sure we don't delete any old archives
            archives_to_delete = self.ARCHIVE_TYPE[archive_type].objects.none()
            n_archives_to_ignore = len(archive_key)

        # get the data to be archived
        archive_data = self.get_archive_data(measurements, archive_type)

        # delete old archives
        deleted_archives = archives_to_delete.delete()

        # create the archive entries
        created_archives = self.ARCHIVE_TYPE[archive_type].objects.bulk_create(
            [self.ARCHIVE_TYPE[archive_type](**archive)
                for archive in archive_data])

        # report back to user
        self.stdout.write(
            f"Deleted {deleted_archives[0]}, "
            f"ignored {n_archives_to_ignore}, and "
            f"created {len(created_archives)} "
            f"{archive_type} archives "
            f"from {format(period_start, '%m-%d-%Y')} "
            f"to {format(period_end, '%m-%d-%Y')}"
        )

    def get_archive_data(self, qs, archive_type):
        """ returns archives given a queryset """
        # group on metric,channel, and time
        grouped_measurements = qs.annotate(
            # first truncate starttime to day/month so we can group on it
            time=self.TIME_TRUNCATOR[archive_type]('starttime')) \
            .values('metric', 'channel', 'time')

        # calculate archive stats
        archive_data = grouped_measurements.annotate(
            mean=Avg('value'),
            median=Percentile('value', percentile=0.5),
            min=Min('value'),
            max=Max('value'),
            stdev=Coalesce(StdDev('value', sample=True), 0,
                           output_field=FloatField()),
            num_samps=Count('value'),
            starttime=Min('starttime'),
            endtime=Max('endtime'),
            # add _id suffix to fields so they can be assigned to
            # Archive's fk directly
            metric_id=F('metric'),
            channel_id=F('channel'),
            p05=Percentile('value', percentile=0.05),
            p10=Percentile('value', percentile=0.10),
            p90=Percentile('value', percentile=0.90),
            p95=Percentile('value', percentile=0.95)
        )

        # select only columns that will be stored in Archive model
        filtered_archive_data = archive_data.values(
            'channel_id', 'metric_id', 'min', 'max', 'mean',
            'median', 'stdev', 'p05', 'p10', 'p90', 'p95',
            'num_samps', 'starttime', 'endtime')

        return filtered_archive_data
