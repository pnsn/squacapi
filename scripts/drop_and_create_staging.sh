#!/usr/bin/env bash
# dump staging, dump prod schema and import to staging.
# Use this script to replicate production schema in order to test migrations


docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
postgres:12.4-alpine \
dropdb -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER squacapi_staging

docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
postgres:12.4-alpine \
createdb -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER squacapi_staging