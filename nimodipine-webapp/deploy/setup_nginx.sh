#!/bin/bash

set -e

supervisorconf=$1/nimodipine-web/nimodipine/deploy/$2/supervisor-nimodipine.conf
nginxconf=$1/nimodipine-web/nimodipine/deploy/$2/nginx-nimodipine

if [ ! -f $supervisorconf ] || [ ! -f $nginxconf ]; then
    echo "Unable to find $supervisorconf or $nginxconf!"
    exit 1
fi

ln -sf $supervisorconf /etc/supervisor/conf.d/nimodipine-$2.conf
ln -sf $nginxconf /etc/nginx/sites-enabled/nimodipine-$2
