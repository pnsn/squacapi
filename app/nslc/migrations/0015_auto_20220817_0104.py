# Generated by Django 3.1.13 on 2022-08-17 01:04

from django.db import migrations, models
import regex_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nslc', '0014_populate_channel_nslc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchingrule',
            name='channel_regex',
            field=regex_field.fields.RegexField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='matchingrule',
            name='location_regex',
            field=regex_field.fields.RegexField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='matchingrule',
            name='network_regex',
            field=regex_field.fields.RegexField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='matchingrule',
            name='station_regex',
            field=regex_field.fields.RegexField(blank=True, max_length=128, null=True),
        ),
        migrations.AddIndex(
            model_name='channel',
            index=models.Index(fields=['nslc'], name='nslc_channe_nslc_dfa3dc_idx'),
        ),
    ]
