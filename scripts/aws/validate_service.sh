#!/bin/bash
set -e
set -o pipefail

#should get 401 (unauthenticate user)
url=https://$DEPLOYMENT_GROUP_NAME.pnsn.org
resp=`curl -sL -w "%{http_code}\\n" "$url" -o /dev/null`

i=0
while [[ $i -lt 5 ]]
do
  if [ $resp == 401 ];then
    echo "Success"
    break
  else
    echo "Not success - $resp"
    ((i++))
    sleep 15
  fi
done

if [[ $i -eq 5 ]]; then
  echo "Validate service failed after 5 attempts"
fi






