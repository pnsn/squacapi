from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import ProgrammingError
from psycopg2.extensions import AsIs
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail

'''
from https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/postgresql-s3-export.html#postgresql-s3-export-access-bucket
something like
select * from aws.query_export_to_s3( \
    'select * from measurement_measurement  where starttime > now()', 
     aws_commons.create_s3_uri('sample-bucket', 'sample-filepath', 'us-west-2') ) ;
'''
class Command(BaseCommand):
    '''
    export partitioned tables to s3 bucket
    args:
        startdate: 
            desc: when to start backup (inclusive)
            format: 'YYYY-MM-DD'
            default: now - 1.day
        enddate:
            when to end backup (inclusive)
            format: 'YYYY-MM-DD'
            default: now - 1.day
            inclusive: yes
        overwrite:
            if exists in s3 bucket, clobber

    '''
    BUCKET_NAME = 'squacapi-backup'
    REGION = 'us-west-2'

    def add_arguments(self, parser):

        parser.add_argument(
            '--start_date',
            default=datetime.now() - timedelta(days=1),
            help="startdate"
        )

    # def select_latest_partition(self):
    #     '''find the lastest partition and return table name as strings
    #     '''
    #     sql = '''
    #         SELECT table_name
    #         FROM information_schema.tables
    #         WHERE table_schema = 'public'
    #         AND table_name like 'measurement_measurement_%'
    #         ORDER BY table_name DESC
    #         LIMIT 1;
    #         '''
    #     with connection.cursor() as cursor:
    #         cursor.execute(sql)
    #         table = cursor.fetchone()
    #         if table is None:
    #             return table
    #         return table[0]

    # def parse_partition_date(self, table_name):
    #     '''extract date from table name and return datetime object'''
    #     date_string = table_name.replace('measurement_measurement_', '')
    #     date = datetime.strptime(date_string, '%Y_%m_%d')
    #     return date

    # def handle(self, *args, **options):
    #     '''method called by manager'''

    #     '''the TableMaker2500Max'''
    #     sql = '''CREATE TABLE measurement_measurement_%s_%s_%s
    #             PARTITION OF measurement_measurement
    #             FOR VALUES FROM (%s) TO (%s);'''

    #     latest_partition = self.select_latest_partition()
    #     if latest_partition is None:
    #         # case where no partitions exist
    #         latest_partition_date = datetime.now() - timedelta(days=1)
    #     else:
    #         latest_partition_date = self.parse_partition_date(latest_partition)
    #     partition_start_date = latest_partition_date
    #     # how many partitions beyond last_partition do we create????
    #     num_partitions = self.MAX_PARTITIONS - \
    #         (latest_partition_date - datetime.now()).days
    #     errors = []
    #     with connection.cursor() as cursor:
    #         sql = '''CREATE TABLE measurement_measurement_%s_%s_%s
    #             PARTITION OF measurement_measurement
    #             FOR VALUES FROM (%s) TO (%s);'''

    #         for i in range(num_partitions):
    #             partition_start_date += timedelta(days=1)
    #             partition_end_date = partition_start_date + timedelta(days=1)
    #             try:
    #                 # NOTE: AsIS required for formating table names

    #                 cursor.execute(sql, [
    #                     AsIs(partition_start_date.strftime("%Y")),
    #                     AsIs(partition_start_date.strftime("%m")),
    #                     AsIs(partition_start_date.strftime("%d")),
    #                     partition_start_date.strftime("%Y-%m-%d"),
    #                     partition_end_date.strftime("%Y-%m-%d")
    #                 ])

    #                 # gant permissions
    #                 sql_grant = '''GRANT ALL PRIVILEGES
    #                     ON TABLE measurement_measurement_%s_%s_%s
    #                     TO %s; '''

    #                 cursor.execute(sql_grant, [
    #                     AsIs(partition_start_date.strftime("%Y")),
    #                     AsIs(partition_start_date.strftime("%m")),
    #                     AsIs(partition_start_date.strftime("%d")),
    #                     AsIs(settings.DATABASES['default']['USER'])])
    #             except ProgrammingError as e:
    #                 errors.append(str(e))

    #     if len(errors) > 0:
    #         error_string = " ".join(errors)
    #         '''set log level to warn to avoid logger noise regarding
    #              file_cache is unavailable when using oauth2client >= 4.0.0
    #         '''
    #         import logging
    #         logging.getLogger(
    #             'googleapicliet.discovery_cache').setLevel(logging.ERROR)

    #         send_mail("Error in measurement table partitioning",
    #                   error_string,
    #                   settings.EMAIL_NO_REPLY,
    #                   [settings.EMAIL_ADMIN, ],
    #                   fail_silently=False)
