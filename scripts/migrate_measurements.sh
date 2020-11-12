#!/usr/bin/env bash
# import sql file for initial partition configuration

docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
postgres:12.4-alpine \
psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d template1 \
-c 'CREATE USER deploy;'


docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
postgres:12.4-alpine \
psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d template1 \
-c 'GRANT ALL PRIVILEGES ON DATABASE squacapi_production TO deploy;'

docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
--mount type=bind,source=/tmp,target=/tmp  postgres:12.4-alpine \
psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d squacapi_production \
-f /tmp/staging-current.sql


docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
postgres:12.4-alpine \
psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d squacapi_production \
-c "DROP TABLE measurement_measurement;"


docker run -it --rm \
--env PGPASSWORD=$SQUAC_PROD_DB_PASS  \
--mount type=bind,source="$(pwd)"/sql,target=/tmp  postgres:12.4-alpine \
psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d squacapi_production \
-f /tmp/measurement.sql
