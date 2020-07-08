# Generated by Django 2.2.12 on 2020-07-08 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_auto_20200629_2201'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='dashboard',
            name='dashboard_d_name_8857a6_idx',
        ),
        migrations.RenameField(
            model_name='dashboard',
            old_name='is_public',
            new_name='share_all',
        ),
        migrations.RenameField(
            model_name='widget',
            old_name='is_public',
            new_name='share_all',
        ),
        migrations.AddField(
            model_name='dashboard',
            name='share_org',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='widget',
            name='share_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='dashboard',
            index=models.Index(fields=['share_all'], name='dashboard_d_share_a_bcc8e7_idx'),
        ),
        migrations.AddIndex(
            model_name='dashboard',
            index=models.Index(fields=['share_org'], name='dashboard_d_share_o_3460ca_idx'),
        ),
    ]
