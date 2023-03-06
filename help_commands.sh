docker compose -f compose up --detach
docker compose -f compose down
#check_updates
statys/openai_bot:0.1

docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower