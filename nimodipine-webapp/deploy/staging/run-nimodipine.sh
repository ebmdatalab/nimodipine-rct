#!/usr/bin/env bash

cd /var/www/nimodipine-staging/nimodipine-rct/nimodipine-webapp/

. /etc/profile.d/nimodipine_staging.sh && exec ../../venv/bin/gunicorn nimodipine.wsgi -c deploy/live/gunicorn-nimodipine-staging.conf.py
