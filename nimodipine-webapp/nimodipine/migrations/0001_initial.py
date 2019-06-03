# Generated by Django 2.0.5 on 2019-06-03 13:23

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MailLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('recipient', models.CharField(db_index=True, max_length=254)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=100), null=True, size=None)),
                ('reject_reason', models.CharField(blank=True, max_length=15, null=True)),
                ('event_type', models.CharField(choices=[('queued', 'queued'), ('sent', 'sent'), ('rejected', 'rejected'), ('failed', 'failed'), ('bounced', 'bounced'), ('deferred', 'deferred'), ('delivered', 'delivered'), ('autoresponded', 'autoresponded'), ('opened', 'opened'), ('clicked', 'clicked'), ('complained', 'complained'), ('unsubscribed', 'unsubscribed'), ('subscribed', 'subscribed'), ('inbound', 'inbound'), ('inbound_failed', 'inbound_failed'), ('unknown', 'unknown')], db_index=True, max_length=15)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'frontend_maillog',
                'managed': False,
            },
        ),
    ]
