'''
List all application crons here. These are imported by settings.
Verify they look correct with 'python {squac_dir}/app/manage.py crontab show'
Reference: https://pypi.org/project/django-crontab/
'''

PRODUCTION_CRONJOBS = [  # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('30 10 * * *', 'django.core.management.call_command',
        ['update_auto_channels']),
    ('0 20 * * *', 'django.core.management.call_command',
        ['create_table_partition']),
    ('5 * * * *', 'django.core.management.call_command', ['evaluate_alarms']),
    ('0 5 * * *', 'django.core.management.call_command', ['s3_query_export']),
    ('0 6 1,10 * *', 'django.core.management.call_command',
        ['archive_measurements', 'month']),
    ('0 7 * * 1', 'django.core.management.call_command',
        ['backfill_archives', 'week', '--overwrite'], {'period_size': 1}),
    ('30 5 * * *', 'django.core.management.call_command',
        ['backfill_archives', 'day', '--overwrite'], {'period_size': 6})
]

STAGING_CRONJOBS = [  # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('30 10 * * *', 'django.core.management.call_command',
        ['update_auto_channels']),
    ('5 * * * *', 'django.core.management.call_command', ['evaluate_alarms']),
    ('0 6 1,10 * *', 'django.core.management.call_command',
        ['archive_measurements', 'month']),
    ('0 7 * * 1', 'django.core.management.call_command',
        ['backfill_archives', 'week', '--overwrite'], {'period_size': 1}),
    ('30 5 * * *', 'django.core.management.call_command',
        ['backfill_archives', 'day', '--overwrite'], {'period_size': 6})
]
