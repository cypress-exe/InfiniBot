#!/bin/bash


daemon="";

echo -n "daemon mode (y/N): ";
read daemonmode;
if [ "$daemonmode" = "y" -o "$daemonmode" = "Y" ]
then
  daemon="-d";
fi

docker run \
  $daemon \
  --name infinibot \
  infinibot:latest \
  "$@"
