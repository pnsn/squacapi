# Generated by Django 2.2.16 on 2020-09-22 23:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('measurement', '0021_auto_20200922_2324'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField()),
                ('message', models.CharField(max_length=255)),
                ('in_alarm', models.BooleanField(default=True)),
                ('alarm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='measurement.Alarms')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['-timestamp'], name='measurement_timesta_d31e16_idx'),
        ),
    ]