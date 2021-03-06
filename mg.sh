#!/bin/bash
#use this to clean up run cruft
#docker rm $(docker ps -a --filter="name=docker_app_run" -q)
 echo $1
if [ "$#" -lt 1 ]; then
  echo "mg.sh: utility to run shell commands via docker-compose
    replaces
    docker-compose run --rm app sh -c python manage.py 'arg1 [arg2] ... [argn]'
    mg.sh shell
    for multiple args use quotes
    mg.sh 'migrate app-name 0001'
    mg.sh 'test && flake8'
    mg.sh help 
    "
    
  exit 1
fi
docker-compose run --rm  app sh -c "python manage.py $1"
