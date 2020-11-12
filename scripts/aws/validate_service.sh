#!/bin/bash
set -e
set -o pipefail

#should get 401 (unauthenticate user)

url=https://$DEPLOYMENT_GROUP_NAME.pnsn.org
if [ `curl -sL -w "%{http_code}\\n" "$url" -o /dev/null` == 401 ];then
    echo "Success"
else
    echo "Failure, rolling back"
    rm $SYMLINK && ln -s $PREVIOUS_RELEASE $SYMLINK
    service $GUNICORN_SERVICE restart
    exit 1
fi

