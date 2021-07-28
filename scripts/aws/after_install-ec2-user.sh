#!/bin/bash

dest=/var/www/releases/$DEPLOYMENT_GROUP_NAME/$DEPLOYMENT_ID
mv /var/www/releases/tmp $dest
aws s3 cp s3://squacapi-config/bash/$DEPLOYMENT_GROUP_NAME.env  $dest/app/.env

#install daemon
curl https://s3.us-west-2.amazonaws.com/aws-xray-assets.us-west-2/xray-daemon/aws-xray-daemon-3.x.rpm -o /home/ec2-user/xray.rpm
yum install -y /home/ec2-user/xray.rpm

echo after s3 call
echo `ls $dest/app/.env `

# virtual env vars
export WORKON_HOME=/var/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
cd $dest
source /usr/local/bin/virtualenvwrapper.sh
source $dest/app/.env
echo dest=$dest
export PATH=$PATH:/usr/local/bin

# delete virtualenv so packages are consistent
rmvirtualenv $DEPLOYMENT_GROUP_NAME
mkvirtualenv $DEPLOYMENT_GROUP_NAME 2>&1
workon $DEPLOYMENT_GROUP_NAME 2>&1

# if staging, bootstrap
if [ $DEPLOYMENT_GROUP_NAME == 'staging-squacapi' ]; then
    python $dest/app/manage.py bootstrap_db --days=7
fi

# both staging and prod use production.txt
pip3 install  -r $dest/requirements/production.txt
python $dest/app/manage.py migrate

# if production, update cronjobs
if [ $DEPLOYMENT_GROUP_NAME == 'squacapi' ]; then
    python $dest/app/manage.py crontab add
fi

# static root most be overridden or it will be added to where current symlink points(previous)
SQUACAPI_STATIC_ROOT=$dest/static python $dest/app/manage.py collectstatic --noinput
deactivate

