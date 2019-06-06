#!/usr/bin/env bash

cd /var/www/nimodipine-staging/nimodipine-web/nimodipine

. /etc/profile.d/nimodipine_staging.sh && exec ../../venv/bin/gunicorn nimodipine.wsgi -c deploy/staging/gunicorn-nimodipine-staging.conf.py
