# Generated by Django 3.1.2 on 2020-11-19 00:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0018_auto_20201013_2006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archive',
            name='archive_type',
            field=models.CharField(choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month')], max_length=8),
        ),
    ]