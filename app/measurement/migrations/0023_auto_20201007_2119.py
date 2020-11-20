# Generated by Django 2.2.16 on 2020-10-07 21:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nslc', '0008_auto_20200728_1909'),
        ('measurement', '0022_auto_20200922_2338'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('interval_type', models.CharField(max_length=15)),
                ('interval_count', models.IntegerField()),
                ('num_channels', models.IntegerField()),
                ('stat', models.CharField(max_length=15)),
                ('channel_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='nslc.Group')),
                ('metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='measurement.Metric')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AlarmThreshold',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('minval', models.FloatField(blank=True, null=True)),
                ('maxval', models.FloatField(blank=True, null=True)),
                ('band_inclusive', models.BooleanField(default=True)),
                ('level', models.CharField(max_length=15)),
                ('alarm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarm_thresholds', to='measurement.Alarm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='alarms',
            name='channel_group',
        ),
        migrations.RemoveField(
            model_name='alarms',
            name='user',
        ),
        migrations.AlterField(
            model_name='alert',
            name='alarm',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='measurement.Alarm'),
        ),
        migrations.DeleteModel(
            name='AlarmMetric',
        ),
        migrations.DeleteModel(
            name='Alarms',
        ),
    ]
