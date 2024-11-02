#!/bin/bash

# Check if "-d" flag is passed
DETACHED=false
for arg in "$@"; do
  if [ "$arg" == "-d" ]; then
    DETACHED=true
    break
  fi
done

volumemount="-v ./generated:/app/generated:rw";

#volumemount="";
#echo -n "perform volume mount [y/N]: ";
#read performvolumemount;
#if [[ "$performvolumemount" =~ [Yy] ]]
#then
#  volumemount="-v $host_volume_dir:$container_data_dir:rw";
#else
##  # a no-op variable, but follows Docker definition so that the
#  # execution below doesn't have an issue.
#  volumemount="-e volumemountspec=none";
#fi
echo "volume_mount: '$volumemount'";

# Run the Docker container with optional detached mode
if [ "$DETACHED" = true ]; then
  docker run -d \
    --name infinibot \
    $volumemount \
    infinibot:latest \
    "${@/-d/}"
  #docker-compose -f .devcontainer/docker-compose.yml up -d
else
  docker run \
    --name infinibot \
    $volumemount \
    infinibot:latest \
    "$@"
  #docker-compose -f .devcontainer/docker-compose.yml up
fi
