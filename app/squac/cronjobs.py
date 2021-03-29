'''list all application  crons here. These are imported by settings'''
from datetime import datetime, timedelta
import pytz

# Data will be exported (and clobbered) for every day going back N days
S3_EXPORT_N_DAYS = 3
s3_export_startdate = (
    datetime.now(tz=pytz.utc) - timedelta(days=S3_EXPORT_N_DAYS)).date()

CRONJOBS=[ # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('0 20 * * *', 'django.core.management.call_command',
        ['create_table_partition']),
    ('5 * * * *', 'django.core.management.call_command', ['evaluate_alarms']),
    ('0 5 * * *', 'django.core.management.call_command', 
        ['s3_query_export', f'--startdate={s3_export_startdate}'])
]
