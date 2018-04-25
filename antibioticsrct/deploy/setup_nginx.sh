#!/bin/bash

set -e

supervisorconf=$1/antibiotics-rct/antibioticsrct/deploy/supervisor-$2.conf
nginxconf=$1/antibiotics-rct/antibioticsrct/deploy/nginx-$2

if [ ! -f $supervisorconf ] || [ ! -f $nginxconf ]; then
    echo "Unable to find $supervisorconf or $nginxconf!"
    exit 1
fi

ln -sf $supervisorconf /etc/supervisor/conf.d/$2.conf
ln -sf $nginxconf /etc/nginx/sites-enabled/$2
