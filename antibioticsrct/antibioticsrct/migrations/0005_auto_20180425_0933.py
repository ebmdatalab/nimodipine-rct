# Generated by Django 2.0.4 on 2018-04-25 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('antibioticsrct', '0004_auto_20180419_0924'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MeasureWording',
        ),
        migrations.AddField(
            model_name='interventioncontact',
            name='blacklisted',
            field=models.BooleanField(default=False),
        ),
    ]
