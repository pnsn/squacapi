#!/bin/bash
set -e
set -o pipefail

# install nginx conf files
aws s3 cp s3://squacapi-config/nginx/squacapi.conf  /etc/nginx/conf.d/
aws s3 cp s3://squacapi-config/nginx/staging-squacapi.conf  /etc/nginx/conf.d/
aws s3 cp s3://squacapi-config/nginx/squacapi-testing.conf  /etc/nginx/conf.d/

# install gunicorn service files
aws s3 cp s3://squacapi-config/gunicorn/gunicorn-production.service /etc/systemd/system/
aws s3 cp s3://squacapi-config/gunicorn/gunicorn-staging.service /etc/systemd/system/
aws s3 cp s3://squacapi-config/gunicorn/gunicorn-testing.service /etc/systemd/system/
chown -R ec2-user:ec2-user /var/www/releases
chmod 775 /var/www/releases

