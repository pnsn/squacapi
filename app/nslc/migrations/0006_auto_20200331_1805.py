# Generated by Django 2.2.11 on 2020-03-31 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nslc', '0005_auto_20191017_1758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='sensor_description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='channel',
            name='station_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]