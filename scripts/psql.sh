 #!/usr/bin/env bash

 if [ $1 ]
    then 
    stage=$1
else
    echo "Usage: psql.sh staging|production|dev"
    exit
fi
docker run -it --env PGPASSWORD=$SQUAC_PROD_DB_PASS --rm postgres:12.4-alpine  psql -h $SQUAC_PROD_DB_HOST  -U $SQUAC_PROD_DB_USER -d squacapi_$1