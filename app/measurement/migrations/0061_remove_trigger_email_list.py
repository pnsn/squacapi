# Generated by Django 3.1.13 on 2023-03-31 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0060_trigger_emails'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='email_list',
        ),
    ]