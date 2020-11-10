#!/bin/bash

set -e
set -o pipefail


export CURRENT_RELEASE=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
export SYMLINK=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink

# track the previous link
export PREVIOUS_RELEASE=`readlink -f $SYMLINK`
echo PREVIOUS_RELEASE > $SYMLINK/previous_release.txt
rm $SYMLINK && ln -s $CURRENT_RELEASE $SYMLINK

GUNICORN_SERVICE=gunicorn-production

if [ $DEPLOYMENT_GROUP_NAME == 'staging-squacapi' ]; then
    GUNICORN_SERVICE=gunicorn-error_test_please_remove
fi

export GUNICORN_SERVICE

service $GUNICORN_SERVICE restart || \
 (rm $SYMLINK && ln -s $PREVIOUS_RELEASE $SYMLINK && echo '$DEPLOYMENT_GROUP_NAME fail' && exit 1)




