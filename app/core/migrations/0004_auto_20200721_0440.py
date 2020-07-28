# Generated by Django 2.2.14 on 2020-07-21 04:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('core', '0003_remove_user_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_org_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='organization.Organization'),
        ),
    ]
