#!/bin/bash

set -e
set -o pipefail

SYMLINK=/var/www/$DEPLOYMENT_GROUP_NAME
# save previous pointer then repoint symlink
cd $SYMLINK
python3 app/manage.py migrate
python3 app/manage.py collectstatic --noinput




