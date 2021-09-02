#!/bin/bash

set -ex
set -o pipefail

export CURRENT_RELEASE=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
export SYMLINK=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink

cd $CURRENT_RELEASE

# track the previous link
export PREVIOUS_RELEASE=`readlink -f $SYMLINK`

rm -f $SYMLINK
ln -s $CURRENT_RELEASE $SYMLINK

GUNICORN_SERVICE=gunicorn-testing

if [ $DEPLOYMENT_GROUP_NAME == 'squacapi' ]; then
    GUNICORN_SERVICE=gunicorn-production
fi

systemctl daemon-reload
PYTHONPATH=$CURRENT_RELEASE service $GUNICORN_SERVICE restart || exit 1
# restart nginx
#only keep 5 versions
cd  /var/www/releases/$DEPLOYMENT_GROUP_NAME && ls -A1t | tail -n +5 | xargs rm -rf




