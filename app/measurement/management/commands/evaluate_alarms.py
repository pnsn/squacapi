from django.core.management.base import BaseCommand
from measurement.models import Monitor

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz


class Command(BaseCommand):
    """
    Command to loop through all alarms and evaluate if they should be turned
    on/off
    """

    def add_arguments(self, parser):
        parser.add_argument('--channel_group', action='append',
                            help='Alarms to check should contain these\
                                  channel_groups',
                            default=[])
        parser.add_argument('--metric', action='append',
                            help='Alarms to check should contain these\
                                  metrics',
                            default=[])

    def handle(self, *args, **options):
        '''method called by manager'''
        # Any monitors in this cycle should have the same endtime
        endtime = datetime.now(tz=pytz.UTC) - relativedelta(
            minute=0, second=0, microsecond=0)

        channel_groups = options['channel_group']
        metrics = options['metric']

        # Get all alarms
        monitors = Monitor.objects.all()

        # Filter for specific channel_groups, metrics if they were selected
        if len(channel_groups) != 0:
            monitors = monitors.filter(channel_group__name__in=channel_groups)
        if len(metrics) != 0:
            monitors = monitors.filter(metric__name__in=metrics)

        # Evaluate each alarm
        for monitor in monitors:
            monitor.evaluate_alarm(endtime=endtime)
