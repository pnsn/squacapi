# Generated by Django 3.1.13 on 2022-05-16 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0022_auto_20220513_2049'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dashboard',
            name='widget',
        ),
        migrations.AddField(
            model_name='widget',
            name='properties',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dashboard',
            name='properties',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
