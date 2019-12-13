#!/bin/bash
#connect to docker db using psql

docker exec -it  squacapi_db  psql -U postgres  squac_dev