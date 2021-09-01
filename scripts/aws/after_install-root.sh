#!/bin/bash
set -ex
set -o pipefail

# install nginx conf files
aws s3 cp s3://squacapi-config/nginx/* /etc/nginx/conf.d/

# install gunicorn service files
aws s3 cp s3://squacapi-config/gunicorn/* /etc/systemd/system/

chown -R ec2-user:ec2-user /var/www/releases
chmod 775 /var/www/releases

