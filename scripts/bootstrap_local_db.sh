#!/usr/bin/env bash
# copy the staging subset to local docker postgres
# docker db container must be running
source app/.env

if [ $1 ]
    then 
    echo "bootstrapping from $1"
else
    echo "Please provide source to bootstrap with"
    echo "bootstrap_local_db.sh staging|local"
    echo "local is a local sql file at /tmp/staging-current.sql"
    echo "and staging is a current snapshot of the staging db"
  exit
fi
if [ $1 = "staging" ]; then
    ssh -i $PEM_FILE $DEPLOY_USER@$DEPLOY_HOST $DUMP_SCRIPT
    scp -i $PEM_FILE $DEPLOY_USER@$DEPLOY_HOST:$DUMP_DIR/staging-current.sql /tmp/
fi
docker exec squacapi_db  psql -U postgres  template1 -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'squac_dev' AND pid <> pg_backend_pid();"
docker exec squacapi_db  psql -U postgres  template1 -c 'DROP DATABASE squac_dev;'
docker exec squacapi_db  psql -U postgres  template1 -c 'CREATE DATABASE squac_dev;'
docker exec squacapi_db  psql -U postgres  template1 -c 'CREATE USER deploy;'
docker exec squacapi_db  psql -U postgres  template1 -c 'GRANT ALL PRIVILEGES ON DATABASE squac_dev TO deploy;'
cat /tmp/staging-current.sql | docker exec -i  squacapi_db  psql -U postgres  squac_dev

