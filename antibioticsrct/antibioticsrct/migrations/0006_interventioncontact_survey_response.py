# Generated by Django 2.0.4 on 2018-04-25 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('antibioticsrct', '0005_auto_20180425_0933'),
    ]

    operations = [
        migrations.AddField(
            model_name='interventioncontact',
            name='survey_response',
            field=models.NullBooleanField(default=None),
        ),
    ]
