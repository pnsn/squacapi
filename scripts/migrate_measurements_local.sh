#!/usr/bin/env bash
# copy the staging subset to local docker postgres
# docker db container must be running
source app/.env

# if [ $1 ]
#     then 
#     echo "bootstrapping from $1"
# else
#     echo "Please provide source to bootstrap with"
#     echo "bootstrap_local_db.sh staging|local"
#     echo "local is a local sql file at /tmp/staging-current.sql"
#     echo "and staging is a current snapshot of the staging db"
#   exit
# fi

docker exec squacapi_db   psql -U postgres  squac_dev -c 'DROP TABLE measurement_measurement;'
cat sql/measurement.sql | docker exec -i  squacapi_db  psql -U postgres  squac_dev


