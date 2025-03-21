./remove_container.bash

./build.bash --use-cache

bash ./run.bash -d

docker exec -it infinibot_container python3 ./src/tests.py