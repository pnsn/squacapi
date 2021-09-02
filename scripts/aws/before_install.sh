#!/bin/bash

set -e
set -o pipefail

# Home base for the app
APP_ROOT=/var/www/$APPLICATION_NAME

# Make tmp folder for codedeploy to place app
mkdir -p $APP_ROOT/tmp

# Make sure releases folder exists
mkdir -p $APP_ROOT/releases

# Ensure there isn't an existing file here
rm -rf $APP_ROOT/tmp/*