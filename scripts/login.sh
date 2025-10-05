#!/usr/bin/env bash

set -eu
set -o pipefail

access_token=$(curl -s -X POST -c cookies.txt localhost:9090/signin \
    -H "Content-Type: application/json" \
    -d '{"username": "richardhapb", "password": "gabytelometo"}' \
    | jq -r ".access_token")


bearer="Bearer $access_token"
auth="Authorization: $bearer"

oauth_link=$(curl -s -w %{redirect_url} -c cookies.txt -b cookies.txt -o /dev/null localhost:9090/google-authorize -H "$auth")

echo "Authorize throught the link: $oauth_link"
echo

link=""

while [ -z "$link" ]; do
    read -e -p "Insert the forwarded link after authorization: " link
    if [ -z "$link" ]; then
        echo "Insert the link correctly"
    fi
done

curl -Ls -c cookies.txt -b cookies.txt "$link" -H "$auth"



