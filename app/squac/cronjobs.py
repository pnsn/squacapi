'''list all application  crons here. These are imported by settings'''

CRONJOBS=[ # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('0 20 * * *', 'django.core.management.call_command',
        ['create_table_partition']),
    ('5 * * * *', 'django.core.management.call_command', ['evaluate_alarms']),
    ('0 5 * * *', 'django.core.management.call_command', ['s3_query_export'])
]
