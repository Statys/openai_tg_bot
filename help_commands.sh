docker compose -f compose up --detach
docker compose -f compose down
#check_updates
statys/openai_bot:0.1

docker run --rm\
  --name watchtower \
  -e WATCHTOWER_POLL_INTERVAL=10 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower --debug

watch -n 1 docker container ps