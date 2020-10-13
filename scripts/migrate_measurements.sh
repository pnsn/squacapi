#!/usr/bin/env bash
# import sql file for initial partition configuration
if [ $1 ]
    then 
    stage=$1
else
    echo "Usage: psql-file.sh staging|production"
    exit
fi

docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER -d squacapi_$stage \
-c "DROP TABLE measurement_measurement;"


docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
--mount type=bind,source="$(pwd)"/sql,target=/tmp  postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER -d squacapi_$stage \
-f /tmp/measurement.sql
