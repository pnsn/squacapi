from django.core.management.base import BaseCommand
from measurement.models import Alarm


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
        self.stdout.write('Evaluating alarms...')

        channel_groups = options['channel_group']
        metrics = options['metric']

        # Get all alarms
        alarms = Alarm.objects.all()

        # Filter for specific channel_groups, metrics if they were selected
        if len(channel_groups) != 0:
            alarms = alarms.filter(channel_group__name__in=channel_groups)
        if len(metrics) != 0:
            alarms = alarms.filter(metric__name__in=metrics)

        # Evaluate each alarm
        for alarm in alarms:
            alarm.evaluate_alarm()

        self.stdout.write(self.style.SUCCESS('Finished checking alarms!'))
