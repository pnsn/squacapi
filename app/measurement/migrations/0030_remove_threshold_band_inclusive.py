# Generated by Django 3.1.2 on 2020-12-02 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0029_merge_20201120_1933'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='threshold',
            name='band_inclusive',
        ),
    ]