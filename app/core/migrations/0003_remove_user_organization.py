# Generated by Django 2.2.12 on 2020-06-03 17:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20200305_0106'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='organization',
        ),
    ]