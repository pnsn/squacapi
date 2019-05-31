#!/bin/bash

 echo $1
if [ "$#" -lt 1 ]; then
  echo "mg.sh: utility to run shell commands via docker-compose
    replaces
    docker-compose run --rm app sh -c python mangage.py [arg1]
    mg.sh shell
    for multiple args use quotes
    mg.sh 'migrate app-name 0001'
    mg.sh 'test && flake8'
    mg.sh help 
    "
    
  exit 1
fi
docker-compose run --rm  app sh -c "python manage.py $1"
