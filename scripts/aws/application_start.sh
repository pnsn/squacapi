#!/bin/bash

set -e
set -o pipefail


export CURRENT_RELEASE=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
export SYMLINK=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink

# track the previous link
export PREVIOUS_RELEASE=`readlink -f $SYMLINK`

rm -f $SYMLINK
ln -s $CURRENT_RELEASE $SYMLINK

GUNICORN_SERVICE=gunicorn-production

if [ $DEPLOYMENT_GROUP_NAME == 'staging-squacapi' ]; then
    GUNICORN_SERVICE=gunicorn-staging
fi

systemctl daemon-reload
PYTHONPATH=$SYMLINK service $GUNICORN_SERVICE restart || exit 1

#only keep 5 versions
cd  /var/www/releases/$DEPLOYMENT_GROUP_NAME && ls -A1t | tail -n +5 | xargs rm -rf




