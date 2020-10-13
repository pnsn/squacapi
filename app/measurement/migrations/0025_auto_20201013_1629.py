# Generated by Django 2.2.16 on 2020-10-13 16:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0024_auto_20201007_2136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alert',
            name='alarm',
        ),
        migrations.AddField(
            model_name='alert',
            name='alarm_threshold',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='measurement.AlarmThreshold'),
            preserve_default=False,
        ),
    ]
