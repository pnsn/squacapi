#!/bin/bash
set -e
set -o pipefail

APP_ROOT=/var/www/squacapi
# install nginx conf files
aws s3 cp s3://squacapi-config/nginx/squacapi-$DEPLOYMENT_GROUP_NAME.conf  /etc/nginx/conf.d/

# install gunicorn service files
aws s3 cp s3://squacapi-config/gunicorn/gunicorn-$DEPLOYMENT_GROUP_NAME.service /etc/systemd/system/
aws s3 cp s3://squacapi-config/gunicorn/gunicorn-$DEPLOYMENT_GROUP_NAME.socket /etc/systemd/system/

# Change owner from root to ec2-user
chown -R ec2-user:ec2-user $APP_ROOT/releases
chmod 775 $APP_ROOT/releases

#ensure there is log file
mkdir -p /var/log/squacapi
chown -R nginx:ec2-user /var/log/squacapi