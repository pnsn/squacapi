from django.core.management import call_command
from django.core.management.base import BaseCommand
import requests
import os


class Command(BaseCommand):
    def load_sample_hourly_metric(self):
        ''' Populates several days of hourly_mean (id=84) metric for several
            stations
        '''
        pass

    def load_sample_latency_metric(self):
        ''' Populates several days of latency metric for several stations '''
        pass

    def handle(self, *args, **kwargs):
        ''' This command flushes all data from db and reloads data from
            fixture files, collects recent measurements from production
        '''
        call_command('flush', '--noinput')
        call_command('loaddata', 'fixtures/fixtures_all.json')
        self.load_sample_hourly_metric()
        self.load_sample_latency_metric()
