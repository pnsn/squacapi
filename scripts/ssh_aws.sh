#!/usr/bin/env bash

if [ $1 ]
    then 
    ip=$1
else
    echo "Must include ip of instance"
    exit
fi

ssh -i $PEM_FILE ec2-user@$ip