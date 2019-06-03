# Generated by Django 2.0.4 on 2018-04-16 14:37

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Intervention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(default=datetime.date.today)),
                ('intervention', models.CharField(choices=[('A', 'A (with content changes)'), ('B', 'B (without content changes)')], max_length=1)),
                ('wave', models.CharField(choices=[('1', '1'), ('2', '2'), ('3', '3')], max_length=1)),
                ('method', models.CharField(choices=[('e', 'Email'), ('p', 'Post'), ('f', 'Fax')], max_length=1)),
                ('practice_id', models.CharField(max_length=6)),
                ('measure_id', models.CharField(max_length=40)),
            ],
            options={
                'ordering': ['created_date', 'intervention', 'method', 'wave', 'practice_id'],
            },
        ),
        migrations.CreateModel(
            name='MeasureWording',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='intervention',
            unique_together={('method', 'wave', 'practice_id')},
        ),
    ]