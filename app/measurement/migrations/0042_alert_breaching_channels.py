# Generated by Django 3.1.12 on 2021-11-16 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0041_auto_20210915_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='breaching_channels',
            field=models.JSONField(null=True),
        ),
    ]