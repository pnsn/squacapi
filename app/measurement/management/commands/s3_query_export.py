'''
from AWS RDS UserGuide - postgresql-s3-export
https://tinyurl.com/3928rmtx
something like
select * from aws_s3.query_export_to_s3( \
    'select * from measurement_measurement  where starttime > now()',\
     aws_commons.create_s3_uri('sample-bucket',\
                               'sample-filepath',\
                               'us-west-2') ) ;

Run command on production server like:
$: python $SQUAC_HOME/app/manage.py s3_query_export

Run command in docker-compose like:
$: docker-compose run --rm app sh -c "python manage.py s3_query_export"
$: ./mg.sh 's3_query_export'

To run locally (must have production db info in .env):
$: ./mg.sh 's3_query_export --env=prod'

To specify date range (inclusive):
$: ./mg.sh 's3_query_export --start_date=YYYY-mm-dd --end_date=YYYY-mm-dd'

To specify single metric (must know metric_id):
$: ./mg.sh 's3_query_export --metric=12'

To not overwrite files if they already exist (default is overwrite):
$: ./mg.sh 's3_query_export --no_overwrite'

'''
from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime, timedelta
from django.conf import settings
import os
import boto3
import botocore
import pytz


class Command(BaseCommand):
    '''
    export partitioned tables to s3 bucket
    args:
        start_date:
            desc: when to start backup (inclusive)
            format: 'YYYY-MM-DD'
            default: now - 3.day
        end_date:
            desc: when to end backup (inclusive)
            format: 'YYYY-MM-DD'
            default: now - 1.day
            inclusive: yes
        metric:
            desc: choose a specific metric to backup
            type: int
            default: -1 (do all)
        no_overwrite:
            desc: Don't clobber if it already exists in s3 bucket
        env:
            desc: Choose environment to get data from, allows local user to
                  backup remote db (default|prod)
            default: 'default'

    '''
    BUCKET_NAME = settings.SQUAC_MEASUREMENTS_BUCKET
    REGION = settings.AWS_DEFAULT_REGION

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date',
            type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
            default=(datetime.now(tz=pytz.utc) - timedelta(days=7)).date(),
            help="When to start backup (inclusive, format: YYYY-MM-DD)"
        )
        parser.add_argument(
            '--end_date',
            type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
            default=(datetime.now(tz=pytz.utc) - timedelta(days=1)).date(),
            help="When to end backup (inclusive, format: YYYY-MM-DD)"
        )
        parser.add_argument(
            '--metric',
            type=int,
            default=-1,
            help="Backup a specific metric, by id"
        )
        parser.add_argument(
            '--no_overwrite',
            action='store_true',
            help="Don't overwrite files on s3 (will overwrite by default)"
        )
        parser.add_argument(
            '--env',
            default='default',
            help='Which env to run this on [default|prod]'
        )

    def handle(self, *args, **kwargs):
        """
        For each day:
            - Get all metrics that have measurements
            - For each metric
                - Execute sql to save all measurements for this metric as an
                  s3 object
                - Path format: raw/YYYY/mm/YYYY_mm_dd_metric_{id}.csv
        """
        sql = '''
            SELECT * FROM aws_s3.query_export_to_s3(
                '
                SELECT * FROM measurement_measurement
                    WHERE metric_id = %s
                        AND starttime >= current_date - %s
                        AND starttime < current_date - %s
                ',
                aws_commons.create_s3_uri(%s, %s, %s),
                options := 'format csv'
            );
        '''
        start_date = kwargs['start_date']
        end_date = kwargs['end_date']

        print(f"Looking from {start_date.strftime('%Y_%m_%d')} "
              f"to {end_date.strftime('%Y_%m_%d')}")

        # Specify environment if running locally (i.e. to backfill)
        env = kwargs['env']
        if env == 'prod':
            settings.DATABASES['prod'] = {
                'ENGINE': 'django.db.backends.postgresql',
                'HOST': os.environ.get('SQUAC_PROD_DB_HOST'),
                'NAME': os.environ.get('SQUAC_PROD_DB_NAME'),
                'USER': os.environ.get('SQUAC_PROD_DB_USER'),
                'PASSWORD': os.environ.get('SQUAC_PROD_DB_PASS'),
            }

        # Verify using correct db
        allowed_dbs = [os.environ.get('SQUAC_PROD_DB_NAME'), ]
        if settings.DATABASES[env]['NAME'] not in allowed_dbs:
            print(f'{env} is not a valid db option!')
            return

        with connections[env].cursor() as cursor:
            # Loop over days
            for kday in range((end_date - start_date).days + 1):
                # current date object in the loop
                cursor_date = start_date + timedelta(days=kday)
                # used for SQL query
                days_before_today = (
                    datetime.now(tz=pytz.utc).date() - cursor_date).days

                # Get all metrics available for this date
                metrics = self.get_db_date_metrics(cursor, cursor_date)

                # Select single metric if requested
                if kwargs['metric'] >= 0:
                    if kwargs['metric'] in metrics:
                        metrics = [kwargs['metric']]
                    else:
                        metrics = []

                for metric in metrics:
                    '''
                    file name format:
                    raw/YYYY/mm/YYYY_mm_dd_metric_{id}.csv
                    '''
                    file_path = (
                        f"raw/{cursor_date.strftime('%Y/%m/%Y_%m_%d')}"
                        f"_metric_{metric}.csv"
                    )
                    print(f"save to {file_path}")

                    # Check overwrite status, does metric file already exist?
                    if kwargs['no_overwrite']:
                        if self.check_s3_file_exists(file_path):
                            print("File already exists, not overwriting!")
                            continue

                    cursor.execute(sql, [
                        metric,
                        days_before_today,
                        days_before_today - 1,
                        self.BUCKET_NAME,
                        file_path,
                        self.REGION
                    ])

    def get_db_date_metrics(self, cursor, cursor_date):
        '''
        Get all metrics for a given date.
        '''
        sql = '''
            SELECT DISTINCT metric_id FROM measurement_measurement
            WHERE starttime >= current_date - %s
                AND starttime < current_date - %s
            ORDER BY metric_id;
        '''
        days_before_today = (
            datetime.now(tz=pytz.utc).date() - cursor_date).days
        cursor.execute(sql, [days_before_today, days_before_today - 1])
        return [res[0] for res in cursor.fetchall()]

    def check_s3_file_exists(self, file_path):
        '''
        Check if file is in the s3 bucket. AWS_ACCESS_KEY_ID and
        AWS_SECRET_ACCESS_KEY should be defined in .env (or elsewhere?) for
        this to work.
        Default return value is False in case there are s3 access errors
        '''
        try:
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(self.BUCKET_NAME)
            objs = list(bucket.objects.filter(Prefix=file_path))
        except botocore.exceptions.NoCredentialsError as e:
            print(e)
            return False
        except botocore.exceptions.ClientError as e:
            print(e)
            return False

        return len(objs) != 0
