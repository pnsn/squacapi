#!/bin/bash
# set -e
# set -o pipefail
dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mv /var/www/releases/tmp $dest
aws s3 cp s3://squacapi-config/bash/$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env
echo after s3 call
echo `ls $dest/app/.env `

# virtual env vars
export WORKON_HOME=/var/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3

source /usr/local/bin/virtualenvwrapper.sh
source $dest/app/.env
echo dest=$dest
export PATH=$PATH:/usr/local/bin
# delete virtualenv so packages are consistent
rmvirtualenv $DEPLOYMENT_GROUP_NAME
mkvirtualenv $DEPLOYMENT_GROUP_NAME 2>&1
workon $DEPLOYMENT_GROUP_NAME || echo test
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate
python $dest/app/manage.py collectstatic --noinput
deactivate



