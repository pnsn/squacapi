#! /usr/bin/env bash
source app/.env
ssh -i $PEM_FILE $DEPLOY_USER@$DEPLOY_HOST $DEPLOY_SCRIPT $1 $2