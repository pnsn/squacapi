#!/bin/bash
set -e
set -o pipefail

#should get 401 (unauthenticate user)
echo SYMLINK$SYMLINK
url=https://$DEPLOYMENT_GROUP_NAME.pnsn.org
resp=`curl -sL -w "%{http_code}\\n" "$url" -o /dev/null`
if [ $resp == 401 ];then
    echo "Success"
else
    echo $resp
    echo "Failure, rolling back"
    rm $SYMLINK && ln -s $PREVIOUS_RELEASE $SYMLINK
    service $GUNICORN_SERVICE restart
    exit 1
fi

