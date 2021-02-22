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