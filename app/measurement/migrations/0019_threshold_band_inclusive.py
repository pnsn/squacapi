# Generated by Django 2.2.16 on 2020-09-22 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0018_alarms'),
    ]

    operations = [
        migrations.AddField(
            model_name='threshold',
            name='band_inclusive',
            field=models.BooleanField(default=True),
        ),
    ]
