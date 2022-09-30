# Generated by Django 3.1.13 on 2022-09-30 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nslc', '0020_auto_20220919_2123'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='channel',
            name='nslc_channe_station_a0d176_idx',
        ),
        migrations.RemoveIndex(
            model_name='channel',
            name='nslc_channe_loc_3c0c29_idx',
        ),
        migrations.RemoveIndex(
            model_name='channel',
            name='nslc_channe_lat_533aec_idx',
        ),
        migrations.RemoveIndex(
            model_name='channel',
            name='nslc_channe_lon_1d0a17_idx',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='elev',
            new_name='elevation',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='lat',
            new_name='latitude',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='loc',
            new_name='location',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='lon',
            new_name='longitude',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='station_code',
            new_name='station',
        ),
        migrations.AlterUniqueTogether(
            name='channel',
            unique_together={('code', 'network', 'station', 'location')},
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['station'], name='nslc_channe_station_8494e8_idx'),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['location'], name='nslc_channe_locatio_6f5e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['latitude'], name='nslc_channe_latitud_da5976_idx'),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['longitude'], name='nslc_channe_longitu_898257_idx'),
        ),
    ]
