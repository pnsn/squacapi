from django.core.management.base import BaseCommand
from django.db.models import (Avg, StdDev, Min, Max, Count, Value, CharField,
                              F, FloatField)
from django.db.models.functions import (ExtractDay, ExtractWeek, ExtractMonth,
                                        Coalesce)
from measurement.models import Measurement, Archive
from measurement.aggregates.percentile import Percentile
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    """ Command for creating archive entries"""

    help = 'Archives Measurements older than the specified age'

    TIME_EXTRACTOR = {
        Archive.ArchiveType.DAY: ExtractDay,
        Archive.ArchiveType.WEEK: ExtractWeek,
        Archive.ArchiveType.MONTH: ExtractMonth,
    }
    """" Django datetime extractors for dealing with portions of datetimes """

    DURATIONS = {
        Archive.ArchiveType.DAY: lambda count: relativedelta(day=count),
        Archive.ArchiveType.WEEK: lambda count: relativedelta(week=count),
        Archive.ArchiveType.MONTH: lambda count: relativedelta(month=count),
    }
    """ functions for generating timesteps of sizes """

    def add_arguments(self, parser):
        parser.add_argument('period_size', type=int,
                            help='number of archives to be created')
        parser.add_argument('archive_type',
                            help='The granularity of the desired archive\
                                 (i.e. day, week, month, etc.)')
        parser.add_argument('--period_end',
                            type=lambda s: datetime.strptime(s, "%m-%d-%Y"),
                            nargs='?', default=datetime.now(),
                            help='the most recent date to be included in\
                                  the archive (format: mm-dd-yyyy)')
        parser.add_argument('--metric', action='append',
                            help='name of the metric to be archived',
                            default=[])

    def handle(self, *args, **kwargs):
        # extract args
        archive_type = kwargs['archive_type']
        metrics = kwargs['metric']
        period_end = kwargs['period_end']
        period_size = kwargs['period_size']
        period_start = period_end - self.DURATIONS[archive_type](period_size)

        # filter down to time range
        measurements = Measurement.objects.filter(
            endtime__date__lte=period_end) \
            .filter(endtime__date__gt=period_start)

        # if specific metrics were selected, filter for them
        if len(metrics) != 0:
            measurements = measurements.filter(
                metric__name__in=metrics)

        # get the data to be archived
        archive_data = self.get_archive_data(measurements, archive_type)

        # create the archive entries
        created_archives = Archive.objects.bulk_create(
            [Archive(**archive) for archive in archive_data])

        # report back to user
        self.stdout.write(f"Created {len(created_archives)} entries \
            for each {archive_type} from {format(period_start, '%m-%d-%Y')} \
            to {format(period_end, '%m-%d-%Y')}")

    def get_archive_data(self, qs, archive_type):
        """ returns archives given a queryset """

        # group on metric,channel, and time
        grouped_measurements = qs.annotate(
            # first add day/week/month/year to tuple so we can group on it
            time=self.TIME_EXTRACTOR[archive_type]('endtime')) \
            .values('metric', 'channel', 'time')

        # calculate archive stats
        archive_data = grouped_measurements.annotate(
            # also annotate type so it can be directly transferred over to
            # Archive
            archive_type=Value(archive_type, CharField(max_length=8)),
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
            channel_id=F('channel'))

        # select only columns that will be stored in Archive model
        filtered_archive_data = archive_data.values(
            'archive_type', 'channel_id', 'metric_id', 'min', 'max', 'mean',
            'median', 'stdev', 'num_samps', 'starttime', 'endtime')

        return filtered_archive_data
