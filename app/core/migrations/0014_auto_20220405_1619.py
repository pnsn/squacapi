# Generated by Django 3.1.12 on 2022-04-05 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_contact_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='user',
        ),
        migrations.DeleteModel(
            name='Contact',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
    ]