# Generated by Django 3.1.13 on 2023-03-27 23:16

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0057_monitor_do_daily_digest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monitor',
            name='stat',
            field=models.CharField(choices=[('count', 'Count'), ('sum', 'Sum'), ('avg', 'Avg'), ('min', 'Min'), ('max', 'Max'), ('minabs', 'MinAbs'), ('maxabs', 'MaxAbs'), ('median', 'Median'), ('p90', 'P90'), ('p95', 'P95')], default='sum', max_length=8),
        ),
    ]