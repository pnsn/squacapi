#!/bin/bash

set -e
set -o pipefail


dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
symlink=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink
PREVIOUS_BUILD=`ls -d $symlink`
rm $symlink && ln -s $dest $symlink

chmod 775 $dest

#try restarting if it doesn't work 
#restart gunicorn
if [ $DEPLOYMENT_GROUP_NAME == 'squacapi' ]; then
    service gunicorn-production restart || rm $symlink && ln -s $PREVIOUS_BUILD $symlink && echo 'prod fail'
else
    service gunicorn-staging restart || rm $symlink && ln -s $PREVIOUS_BUILD $symlink && echo 'staging fail'
fi

