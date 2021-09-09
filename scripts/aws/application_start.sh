#!/bin/bash

set -ex
set -o pipefail

APP_ROOT=/var/www/squacapi
CURRENT_RELEASE=$APP_ROOT/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
SYMLINK=$APP_ROOT/$DEPLOYMENT_GROUP_NAME

cd $CURRENT_RELEASE

rm -f $SYMLINK
ln -s $CURRENT_RELEASE $SYMLINK

GUNICORN_SERVICE=gunicorn-$DEPLOYMENT_GROUP_NAME

# Restart gunicorn 
systemctl daemon-reload
systemctl enable $GUNICORN_SERVICE.socket
systemctl restart $GUNICORN_SERVICE.socket $GUNICORN_SERVICE.service

# Check if valid and restart nginx
nginx -t
systemctl restart nginx

# Only keep 5 versions
cd  $APP_ROOT/releases/$DEPLOYMENT_GROUP_NAME && ls -A1t | tail -n +5 | xargs rm -rf
