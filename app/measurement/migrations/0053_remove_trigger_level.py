# Generated by Django 3.1.12 on 2022-04-05 16:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0052_auto_20220405_1606'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='level',
        ),
    ]