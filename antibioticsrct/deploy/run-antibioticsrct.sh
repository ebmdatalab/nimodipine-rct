#!/usr/bin/env bash

cd /var/www/antibioticsrct/antibiotics-rct/antibioticsrct

. /etc/profile.d/antibioticsrct_live.sh && exec ../../venv/bin/gunicorn antibioticsrct.wsgi -c deploy/gunicorn-antibioticsrct.conf.py
