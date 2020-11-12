from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        ''' This command flushes all data from db and reloads data from
            fixture files, collects recent measurements from production
        '''
        call_command('flush', '--noinput')
        call_command('loaddata', 'fixtures/fixtures_all.json')
