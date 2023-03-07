docker compose -f compose up --detach
docker compose -f compose down
#check_updates
docker run -d --rm\
  --name watchtower \
  -e WATCHTOWER_POLL_INTERVAL=120 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower

watch -n 1 docker container ps