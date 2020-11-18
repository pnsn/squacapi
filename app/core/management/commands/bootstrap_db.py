from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from numpy import random
from datetime import datetime as dt, time, timedelta

from measurement.models import Metric, Measurement
from nslc.models import Channel


class Command(BaseCommand):
    def sample_values(self, mu_min, mu_max, sigma_min, sigma_max, size):
        ''' Get a sampling of values from a normal distribution '''
        mu = random.uniform(mu_min, mu_max)
        sigma = random.uniform(sigma_min, sigma_max)
        return list(random.normal(mu, sigma, size))

    def load_values(self, values, metric, channel, user, time_decrement):
        ''' Load measurment values for a given channel '''
        print(len(values))
        endtime = make_aware(
            dt.now().replace(second=0, microsecond=0)
        )
        endtime -= time_decrement * len(values)
        starttime = endtime - time_decrement

        for value in values:
            Measurement.objects.create(
                metric=metric,
                channel=channel,
                value=value,
                starttime=starttime,
                endtime=endtime,
                user=user
            )
            endtime += time_decrement
            starttime += time_decrement

    def load_sample_hourly_metric(self):
        ''' Populates several days of hourly_mean metric for all 10 channels in
            fixture file
        '''
        user = get_user_model().objects.get(email='loader@pnsn.org')
        metric_url = 'https://github.com/pnsn/'
        metric_url += 'station_metrics/blob/master/station_metrics.md'
        metric, _ = Metric.objects.get_or_create(
            name='hourly_mean',
            defaults={
                'code': 'hourly_mean',
                'description': 'Hourly mean of raw data',
                'unit': 'count',
                'default_minval': -1e9,
                'default_maxval': 1e9,
                'reference_url': metric_url,
                'user': user
            }
        )
        channels = Channel.objects.all()

        for channel in channels:
            print(f'Loading hourly_mean measurements for {channel}')
            values = self.sample_values(8e4, 9e4, 1e3, 3e3, 168)
            self.load_values(values, metric, channel, user, timedelta(hours=1))

    def load_sample_latency_metric(self):
        ''' Populates several days of latency metric for several stations '''
        user = get_user_model().objects.get(email='loader@pnsn.org')
        metric_url = 'https://github.com/pnsn/dataflow_metrics/'
        metric_url += 'blob/master/docs/pnsn_dataflow_metrics.md'
        desc = 'latency as defined by time between measurement end of packet '
        desc += 'plus half of packet length, measured on ewserver1 for 10 '
        desc += 'minutes and averaged.'
        metric, _ = Metric.objects.get_or_create(
            name='export_ring_latency',
            defaults={
                'code': 'export_ring_latency',
                'description': desc,
                'unit': 'seconds',
                'default_minval': 0.0,
                'default_maxval': 5.0,
                'reference_url': metric_url,
                'user': user
            }
        )
        channels = Channel.objects.all()

        for channel in channels:
            print(f'Loading export_ring_latency measurements for {channel}')
            values = self.sample_values(1, 4, 0.1, 0.3, 1008)
            self.load_values(
                values, metric, channel, user, timedelta(minutes=10))

    def handle(self, *args, **kwargs):
        ''' This command flushes all data from db and reloads data from
            fixture files, generates 7 days of hourly_mean and
            export_ring_latency measurements for all channels in fixture
        '''
        call_command('flush', '--noinput')
        call_command('loaddata', 'fixtures/fixtures_all.json')
        self.load_sample_hourly_metric()
        self.load_sample_latency_metric()
        print('Database loading complete')
