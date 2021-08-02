from django.core.management.base import BaseCommand
from django.db.models import (Avg, StdDev, Min, Max, Count, F, FloatField,
                              Value as V)
from django.db.models.functions import (TruncDay, TruncMonth, Coalesce,
                                        Concat)
from measurement.models import (Measurement, ArchiveDay, ArchiveMonth)
from measurement.aggregates.percentile import Percentile
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz


class Command(BaseCommand):
    """ Command for creating archive entries"""

    help = 'Archives Measurements older than the specified age'

    TIME_TRUNCATOR = {
        'day': TruncDay,
        'month': TruncMonth,
    }
    """" Django datetime extractors for dealing with portions of datetimes """

    DURATIONS = {
        'day': lambda count: relativedelta(days=count),
        'month': lambda count: relativedelta(months=count),
    }
    """ functions for generating timesteps of sizes """

    ARCHIVE_TYPE = {
        'day': ArchiveDay,
        'month': ArchiveMonth
    }
    """ Types of archive """

    def add_arguments(self, parser):
        parser.add_argument('period_size', type=int,
                            help='number of archives to be created')
        parser.add_argument('archive_type',
                            choices=['day', 'month'],
                            help=('The granularity of the desired archive '
                                  '(i.e. day, month, etc.)'))
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
        period_size = kwargs['period_size']
        period_start = period_end - self.DURATIONS[archive_type](period_size)

        # if archive_type is month, adjust period start/end to go from 1st day
        # of the month
        if archive_type == 'month':
            period_end = period_end.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
            period_start = period_start.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)

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
            archives_to_ignore = 0
            archives_to_delete = archives
            if len(metrics) != 0:
                archives_to_delete = archives_to_delete.filter(
                    metric_id__in=metrics)
        else:
            # exclude measurements that already have archives. This only works
            # correctly for a single time period
            archive_key = archives.annotate(
                m_c=Concat('metric_id', V(' '), 'channel_id')).values('m_c')
            measurements = measurements.annotate(
                m_c=Concat('metric_id', V(' '), 'channel_id')).exclude(
                m_c__in=archive_key)
            # make sure we don't delete any old archives
            archives_to_delete = self.ARCHIVE_TYPE[archive_type].objects.none()
            archives_to_ignore = len(archive_key)

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
            f"ignored {archives_to_ignore}, and "
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
