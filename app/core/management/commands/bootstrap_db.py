'''
Command bootstraps a development database using fixture file and loads
random sampling of hourly and latency measurements for the 10 channels in the
fixture.

Run command in docker-compose like:
$: docker-compose run --rm app sh -c "python manage.py bootstrap_db --days=7"
$: ./mg.sh 'bootstrap_db --days=7'
This command is meant to be run after dropping a db, which must be done
in seperate process to prevent touching prod.
process checks for allowed dbs, migrates, then stubs out data
to update test account passwords use
python manage.py changepassword user@pnsn.org
Then run
./mg.sh "dumpdata core.user --indent=2 > fixtures/core_user.json"
Then cut and past into all

Local:
docker rm squacapi_db (only if you want to remove an existing container)
./mg.sh 'bootstrap_db --days=7'
docker-compose up

Staging: (must have access):
For staging, use ./scripts/drop_and_create_staging.sh
Then
./mg.sh 'bootstrap_db --days=7 --env=staging'

'''
import os
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from numpy import random
from datetime import datetime as dt, timedelta
from django.conf import settings

from measurement.models import Metric, Measurement
from nslc.models import Channel


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            default=7,
            help='Number of days of measurements to generate'
        )
        parser.add_argument(
            '--env',
            default='default',
            help='which env to run this [default|staging]'
        )

    def sample_values(self, mu_min, mu_max, sigma_min, sigma_max, size):
        ''' Get a sampling of values from a normal distribution '''
        mu = random.uniform(mu_min, mu_max)
        sigma = random.uniform(sigma_min, sigma_max)
        return list(random.normal(mu, sigma, size))

    def load_values(self, values, metric, channel, user, time_decrement):
        ''' Load measurment values for a given channel '''
        endtime = make_aware(
            dt.now().replace(second=0, microsecond=0)
        )
        if time_decrement.seconds == 600:
            endtime.replace(minute=(endtime.minute // 10) * 10)
        else:
            endtime.replace(minute=0)
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

    def load_sample_hourly_metric(self, kwargs):
        ''' Populates several days of hourly_mean metric for all 10 channels in
            fixture file
        '''
        # Params controlling the normal distribution sample for hourly_mean
        mu_min = 8e4
        mu_max = 9e4
        sigma_min = 1e3
        sigma_max = 5e3
        num_samples = int(kwargs['days']) * 24

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
            values = self.sample_values(
                mu_min, mu_max, sigma_min, sigma_max, num_samples)
            self.load_values(values, metric, channel, user, timedelta(hours=1))

    def load_sample_latency_metric(self, kwargs):
        ''' Populates several days of latency metric for several stations '''
        # Params controlling the normal distribution sample for latency
        mu_min = 1
        mu_max = 4
        sigma_min = 0.1
        sigma_max = 0.3
        num_samples = int(kwargs['days']) * 24 * 6

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
            values = self.sample_values(
                mu_min, mu_max, sigma_min, sigma_max, num_samples)
            self.load_values(
                values, metric, channel, user, timedelta(minutes=10))

    def handle(self, *args, **kwargs):
        ''' This command ensures that this is the staging db,
            flushes all data from db and reloads data from
            fixture files, generates given days, default 7, of
            hourly_mean and export_ring_latency measurements
            for all channels in fixture
        '''
        # don't want this in setting file. This is meant to run from local
        env = kwargs['env']
        if env == 'staging':
            settings.DATABASES['staging'] = {
                'ENGINE': 'django.db.backends.postgresql',
                'HOST': os.environ.get('SQUAC_STAGING_DB_HOST'),
                'NAME': 'squacapi_staging',
                'USER': os.environ.get('SQUAC_STAGING_DB_USER'),
                'PASSWORD': os.environ.get('SQUAC_STAGING_DB_PASS')
            }
        allowed_dbs = ['squac_dev', 'squacapi_staging']
        # set database to staging
        if settings.DATABASES[env]['NAME'] in allowed_dbs:
            print(env)
            # run migrations
            call_command('migrate', f'--database={env}')
            # FIXME The fixture data need to be loaded in a single call
            # to avoid fk dependency errors. Currently the single file is
            # built by cutting and pasting. This file should assemble the json
            # into a single file
            for fix in ['all']:
                call_command('loaddata', f'fixtures/{fix}.json',
                             f'--database={env}')
            self.load_sample_hourly_metric(kwargs) 
            self.load_sample_latency_metric(kwargs)
            print('Database loading complete')
