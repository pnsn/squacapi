#!/bin/bash
#connect to docker db using psql

docker exec -it  squac_db_1  psql -U postgres  app
