#!/bin/bash

#  --label "build.git_branch=$git_branch" \
docker build -f ./.devcontainer/Dockerfile \
  --pull --no-cache --force-rm \
  -t infinibot:latest \
  ./
if [ $? != 0 ]
then
  echo "ERROR: Dockerbuild failed.";
  exit 1;
fi