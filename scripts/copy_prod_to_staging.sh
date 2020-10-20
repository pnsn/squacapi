#!/usr/bin/env bash
# dump all production data except full measurementes from prod to staging
#how many of interval
num=2
#interval
interval=hours

docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
postgres:12.4-alpine \
dropdb -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_staging

docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
postgres:12.4-alpine \
createdb -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_staging


docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
postgres:12.4-alpine \
pg_dump -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_production > \
/tmp/prod.sql

docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
--mount type=bind,source=/tmp,target=/tmp \
postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_staging \
-f /tmp/prod.sql


docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
postgres:12.4-alpine \
pg_dump -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_production \
--exclude-table=measurement_measurement \
--exclude-table=measurement_archive  \
> /tmp/data.sql

docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
--mount type=bind,source=/tmp,target=/tmp \
postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_staging \
-f /data/data.sql


# use stdout of one docker to update by stdin of other container. 
docker run -it --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
-a stdin -a stdout -a stderr \
postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER -d squacapi_production \
-c "COPY(SELECT * FROM measurement_measurement  WHERE starttime > now() \
    - interval '$num $interval') TO STDOUT;" | docker run -i --rm \
--env PGPASSWORD=$SQUAC_DB_PASS  \
-a stdin -a stdout -a stderr \
postgres:12.4-alpine \
psql -h $SQUAC_DB_HOST  -U $SQUAC_DB_USER squacapi_staging \
-c "COPY measurement_measurement FROM  STDIN;"

