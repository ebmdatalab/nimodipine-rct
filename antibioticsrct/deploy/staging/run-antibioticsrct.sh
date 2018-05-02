#!/usr/bin/env bash

cd /var/www/antibioticsrct-staging/antibiotics-rct/antibioticsrct

. /etc/profile.d/antibioticsrct_staging.sh && exec ../../venv/bin/gunicorn antibioticsrct.wsgi -c deploy/staging/gunicorn-antibioticsrct-staging.conf.py
