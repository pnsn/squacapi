# Generated by Django 3.1.12 on 2022-01-13 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('measurement', '0048_auto_20220113_1639'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trigger',
            old_name='maxval',
            new_name='val2',
        ),
    ]
