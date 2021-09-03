#!/bin/bash

set -e
set -o pipefail

# Home base for the app
APP_ROOT=/var/www/squacapi

# Make tmp folder for codedeploy to place app
mkdir -p $APP_ROOT/releases/$DEPLOYMENT_GROUP_NAME/tmp
# Ensure there isn't an existing file here
rm -rf $APP_ROOT/releases/tmp