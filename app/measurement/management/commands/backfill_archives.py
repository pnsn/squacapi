from django.core.management.base import BaseCommand
from django.core.management import call_command

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
"""
Run command on production server like:
$: python app/manage.py backfill_archives day --start_time=03-01-2021

Run command locally like:
$: docker-compose run --rm app sh -c "python manage.py backfill_archives ..."
$: ./mg.sh 'backfill_archives month --start_time=03-01-2021-'
"""


class Command(BaseCommand):
    """
    Command to call archive_measurements multiple times (for backfilling)
    """

    DURATIONS = {
        'day': relativedelta(days=1),
        'month': relativedelta(months=1),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            'archive_type',
            choices=['day', 'month']
        )
        parser.add_argument(
            '--start_time',
            type=lambda s: pytz.utc.localize(datetime.strptime(s, "%m-%d-%Y")),
            nargs='?',
            default=(
                datetime.now(tz=pytz.utc) - relativedelta(days=3)).replace(
                hour=0, minute=0, second=0, microsecond=0),
            help="When to start calling backup (inclusive, format: MM-DD-YYYY)"
        )
        parser.add_argument(
            '--end_time',
            type=lambda s: pytz.utc.localize(datetime.strptime(s, "%m-%d-%Y")),
            nargs='?',
            default=datetime.now(tz=pytz.utc).replace(
                hour=0, minute=0, second=0, microsecond=0),
            help="When to stop calling backup (inclusive, format: MM-DD-YYYY)"
        )

    def handle(self, *args, **kwargs):
        '''method called by manager'''
        archive_type = kwargs['archive_type']
        current_time = kwargs['start_time']
        end_time = kwargs['end_time']

        self.stdout.write(
            f'Calling archive_measurement for each {archive_type} from'
            f' {current_time.strftime("%m-%d-%Y")} to'
            f' {end_time.strftime("%m-%d-%Y")}'
        )

        while current_time <= end_time:
            call_command('archive_measurements',
                         archive_type,
                         f'--period_end={current_time.strftime("%m-%d-%Y")}',
                         stdout=self.stdout)

            current_time = current_time + self.DURATIONS[archive_type]
