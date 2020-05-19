#! /usr/bin/env bash
source app/.env
ssh $DEPLOY_USER@$DEPLOY_HOST $DEPLOY_SCRIPT $1 $2

scp build_dir $DEPLOY_USER@$DEPLOY_HOST:$DEST_DIR 