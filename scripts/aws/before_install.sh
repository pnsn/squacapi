#!/bin/bash

set -e
set -o pipefail


mkdir -p /var/www/releases/tmp
#ensure there isn't an existing file here
rm -rf /var/www/releases/tmp/*