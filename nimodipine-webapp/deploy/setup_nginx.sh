#!/bin/bash

set -e

supervisorconf=$1/antibiotics-rct/antibioticsrct/deploy/$2/supervisor-antibioticsrct.conf
nginxconf=$1/antibiotics-rct/antibioticsrct/deploy/$2/nginx-antibioticsrct

if [ ! -f $supervisorconf ] || [ ! -f $nginxconf ]; then
    echo "Unable to find $supervisorconf or $nginxconf!"
    exit 1
fi

ln -sf $supervisorconf /etc/supervisor/conf.d/antibioticsrct-$2.conf
ln -sf $nginxconf /etc/nginx/sites-enabled/antibioticsrct-$2
