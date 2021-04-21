# Generated by Django 3.1.8 on 2021-04-21 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_auto_20201203_0042'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboard',
            name='archive_type',
            field=models.CharField(choices=[('raw', 'Raw'), ('hour', 'Hour'), ('day', 'Day'), ('week', 'Week'), ('month', 'Month')], default='raw', max_length=8),
        ),
    ]
