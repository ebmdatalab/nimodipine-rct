# Generated by Django 2.0.4 on 2018-05-03 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nimodipine', '0009_auto_20180503_0902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intervention',
            name='receipt',
            field=models.NullBooleanField(default=None),
        ),
    ]