# Generated by Django 2.2.6 on 2019-10-08 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nslc', '0003_auto_20191006_1753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='scale_units',
            field=models.CharField(default='M/S', max_length=32),
        ),
    ]
