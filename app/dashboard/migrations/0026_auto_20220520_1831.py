# Generated by Django 3.1.13 on 2022-05-20 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0025_auto_20220516_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='stat',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='widget',
            name='layout',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='widget',
            name='properties',
            field=models.JSONField(null=True),
        ),
    ]
