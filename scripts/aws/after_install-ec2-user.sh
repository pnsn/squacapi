#!/bin/bash
set -ex
set -o pipefail

dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mkdir -p $dest
mv /var/www/releases/tmp/* $dest
aws s3 cp s3://squacapi-config/bash/$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env
source $dest/app/.env

echo after s3 call
echo `ls $dest/app/.env `

# virtual env vars
export WORKON_HOME=/var/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv
source /usr/local/bin/virtualenvwrapper.sh
export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin

echo dest=$dest
cd $dest
# delete virtualenv so packages are consistent
rmvirtualenv $DEPLOYMENT_GROUP_NAME
mkvirtualenv $DEPLOYMENT_GROUP_NAME 2>&1
workon $DEPLOYMENT_GROUP_NAME 2>&1

# if staging, bootstrap
if [ $DEPLOYMENT_GROUP_NAME == 'staging-squacapi' ]; then
    python $dest/app/manage.py bootstrap_db --days=7
fi

echo "PIP INSTLL"
# both staging and prod use production.txt
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate

# if production, update cronjobs
if [ $DEPLOYMENT_GROUP_NAME == 'squacapi' ]; then
    python $dest/app/manage.py crontab -r
    python $dest/app/manage.py crontab add
fi

# static root most be overridden or it will be added to where current symlink points(previous)
SQUACAPI_STATIC_ROOT=$dest/static python $dest/app/manage.py collectstatic --noinput
deactivate

