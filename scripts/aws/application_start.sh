#!/bin/bash

set -e
set -o pipefail


ln -s /var/www/pnsn_web/releases/$DEPLOYMENT_ID /var/www/pnsn_web/current
ln -s /var/www/pnsn_web/shared/config/s3.yml /var/www/pnsn_web/releases/$DEPLOYMENT_ID/config/s3.yml
/bin/touch /var/www/pnsn_web/current/tmp/restart.txt

#update crons
cd /var/www/pnsn_web/current && /usr/local/bin/bundle exec whenever --update-crontab --set "environment=production" -i "production"
