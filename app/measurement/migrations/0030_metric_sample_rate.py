# Generated by Django 3.1.2 on 2020-12-09 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0029_merge_20201120_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='sample_rate',
            field=models.IntegerField(default=3600),
        ),
    ]
