# Generated by Django 2.0.4 on 2018-04-19 09:24

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nimodipine', '0003_auto_20180418_0849'),
    ]

    operations = [
        migrations.AddField(
            model_name='intervention',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='intervention',
            name='measure_id',
            field=models.CharField(default='ktt9_cephalosporins', max_length=40),
        ),
    ]