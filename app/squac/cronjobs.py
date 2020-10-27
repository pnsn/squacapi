'''list all application  crons here. These are imported by settings'''

CRONJOBS=[ # noqa
    ('0 10 * * *', 'django.core.management.call_command', ['load_from_fdsn']),
    ('0 20 * * *', 'django.core.management.call_command',
        ['create_table_partitions'])
]
