# Generated by Django 3.1.12 on 2022-01-13 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0047_auto_20220113_0052'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trigger',
            name='minval',
        ),
        migrations.AddField(
            model_name='trigger',
            name='val1',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
