# Generated by Django 3.1.2 on 2020-12-31 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0030_remove_threshold_band_inclusive'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='name',
            field=models.CharField(default='', max_length=255),
        ),
    ]