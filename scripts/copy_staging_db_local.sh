#!/usr/bin/env bash
# copy the staging subset to local
# docker db container must be running
source app/.env

ssh $DEPLOY_USER@$DEPLOY_HOST $DUMP_SCRIPT
scp $DEPLOY_USER@$DEPLOY_HOST:$DUMP_DIR/staging-current.sql /tmp/
docker exec squacapi_db  psql -U postgres  template1 -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'squac_dev' AND pid <> pg_backend_pid();"
docker exec squacapi_db  psql -U postgres  template1 -c 'DROP DATABASE squac_dev;'
docker exec squacapi_db  psql -U postgres  template1 -c 'CREATE DATABASE squac_dev;'
cat /tmp/staging-current.sql | docker exec -i  squacapi_db  psql -U postgres  squac_dev

