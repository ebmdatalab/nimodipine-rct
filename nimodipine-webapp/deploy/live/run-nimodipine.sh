#!/usr/bin/env bash

cd /var/www/nimodipine/nimodipine-rct/nimodipine-webapp/

. /etc/profile.d/nimodipine_live.sh && exec ../../venv/bin/gunicorn nimodipine.wsgi -c deploy/live/gunicorn-nimodipine.conf.py
