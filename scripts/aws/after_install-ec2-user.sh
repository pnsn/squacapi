#!/bin/bash
set -e
set -o pipefail
dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mv /var/www/releases/tmp $dest
cd $dest

VIRTUALENVWRAPPER_PYTHON=/var/.virtualenvs/$DEPLOYMENT_GROUP_NAME/bin/python
source `which virtualenvwrapper.sh`
workon $DEPLOYMENT_GROUP_NAME
source $dest/app/.env
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate
python $dest/app/manage.py collectstatic --noinput
deactivate



