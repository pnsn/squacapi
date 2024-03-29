#!/bin/bash
APP_ROOT=/var/www/squacapi
dest=$APP_ROOT/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mkdir -p $dest

# Move app out of tmp and into destination
mv $APP_ROOT/releases/tmp/* $dest

# Copy environment file
aws s3 cp s3://squacapi-config/bash/squacapi-$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env
source $dest/app/.env

echo after s3 call
echo `ls $dest/app/.env `

# virtual env vars
export WORKON_HOME=/var/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin

echo dest=$dest
cd $dest

# delete virtualenv so packages are consistent
rmvirtualenv squacapi-$DEPLOYMENT_GROUP_NAME
mkvirtualenv squacapi-$DEPLOYMENT_GROUP_NAME 2>&1
workon squacapi-$DEPLOYMENT_GROUP_NAME 2>&1

# if staging, bootstrap
if [ $DEPLOYMENT_GROUP_NAME == 'staging' ]; then
    python $dest/app/manage.py bootstrap_db --days=7
fi

# All groups use production.txt
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate

# if production, update cronjobs
if [ $DEPLOYMENT_GROUP_NAME == 'jobs' ] || [ $DEPLOYMENT_GROUP_NAME == 'staging' ]; then
    echo 'Cronjobs enabled'
    python $dest/app/manage.py crontab remove
    python $dest/app/manage.py crontab add
fi

# static root must be overridden or it will be added to where current symlink points(previous)
SQUACAPI_STATIC_ROOT=$dest/static python $dest/app/manage.py collectstatic --noinput
deactivate

