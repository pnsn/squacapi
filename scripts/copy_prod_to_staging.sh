#!/usr/bin/env bash
# dump all production data except full measurementes from prod to staging
path=/usr/pgsql-10/bin
#how many of interval
num=2
#interval
interval=hours
$path/dropdb squacapi_staging
$path/createdb squacapi_staging

$path/pg_dump --schema-only squacapi_production | psql -d squacapi_staging

$path/pg_dump --data-only --exclude-table=measurement_measurement --exclude-table=measurement_archive  squacapi_production | \
psql -d squacapi_staging

$path/psql -d squacapi_production -c "COPY(SELECT * FROM measurement_measurement  WHERE starttime > now() - interval '$num $interval') to STDOUT;" | \
$path/psql -d squacapi_staging -c "COPY measurement_measurement FROM  STDIN;"

$path/psql -d squacapi_production -c "COPY(SELECT * FROM measurement_archive  WHERE starttime  > now() - interval '$num $interval') to STDOUT;" | \
$path/psql -d squacapi_staging -c "COPY measurement_archive FROM  STDIN;"
