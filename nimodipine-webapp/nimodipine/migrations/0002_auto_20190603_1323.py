# Generated by Django 2.0.5 on 2019-06-03 13:23

import datetime
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nimodipine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Intervention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(default=datetime.date.today)),
                ('method', models.CharField(choices=[('e', 'Email'), ('p', 'Post'), ('f', 'Fax')], max_length=1)),
                ('practice_id', models.CharField(max_length=6)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('hits', models.IntegerField(default=0)),
                ('sent', models.BooleanField(default=False)),
                ('generated', models.BooleanField(default=False)),
                ('receipt', models.NullBooleanField(default=None)),
            ],
            options={
                'ordering': ['created_date', 'method', 'practice_id'],
            },
        ),
        migrations.CreateModel(
            name='InterventionContact',
            fields=[
                ('practice_id', models.CharField(max_length=6, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('address1', models.CharField(blank=True, max_length=100, null=True)),
                ('address2', models.CharField(blank=True, max_length=100, null=True)),
                ('address3', models.CharField(blank=True, max_length=100, null=True)),
                ('address4', models.CharField(blank=True, max_length=100, null=True)),
                ('postcode', models.CharField(blank=True, max_length=9, null=True)),
                ('email', models.EmailField(blank=True, max_length=200, null=True)),
                ('fax', models.CharField(blank=True, max_length=25, null=True)),
                ('normalised_fax', models.CharField(blank=True, max_length=25, null=True)),
                ('blacklisted', models.BooleanField(default=False)),
                ('survey_response', models.NullBooleanField(default=None)),
            ],
        ),
        migrations.AddField(
            model_name='intervention',
            name='contact',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nimodipine.InterventionContact'),
        ),
        migrations.AlterUniqueTogether(
            name='intervention',
            unique_together={('method', 'practice_id')},
        ),
    ]