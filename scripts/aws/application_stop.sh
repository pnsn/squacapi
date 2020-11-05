#!/bin/bash

dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
symlink=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink
export PREVIOUS_BUILD=`ls $symlink`
rm $symlink && ln -s $dest $symlink

#try restarting if it doesn't work 
#restart gunicorn
if [ $DEPLOYMENT_GROUP_NAME == 'squacapi' ]; then
    service gunicorn-production restart || rm $symlink && ln -s $PREVIOUS_BUILD $symlink
else
    service gunicorn-staging restart || rm $symlink && ln -s $PREVIOUS_BUILD $symlink
fi

