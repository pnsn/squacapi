# Generated by Django 3.1.13 on 2022-08-16 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nslc', '0013_channel_nslc'),
    ]

    def add_nslc(apps, schema_editor):
        ChannelModel = apps.get_model('nslc', 'Channel')

        for c in ChannelModel.objects.all():
            c.nslc = str(c.network_id) + "." + \
                c.station_code + "." + \
                c.loc + "." + c.code
            c.save(update_fields=['nslc'])

    operations = [
        migrations.RunPython(add_nslc, reverse_code=migrations.RunPython.noop)
    ]
