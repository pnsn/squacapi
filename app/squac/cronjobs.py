'''
List all application crons here. These are imported by settings.
Verify they look correct with 'python {squac_dir}/app/manage.py crontab show'
Reference: https://pypi.org/project/django-crontab/
'''

CRONJOBS=[ # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('0 20 * * *', 'django.core.management.call_command',
        ['create_table_partition']),
    ('5 * * * *', 'django.core.management.call_command', ['evaluate_alarms']),
    ('0 5 * * *', 'django.core.management.call_command', ['s3_query_export']),
    ('0 6 1 * *', 'django.core.management.call_command',
        ['archive_measurements', '1', 'month']),
    ('10 0,6 * * *', 'django.core.management.call_command',
        ['archive_measurements', '1', 'day'])
]
