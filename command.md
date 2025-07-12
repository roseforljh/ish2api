git pull origin main

docker rm -f ish2api-proxy-container

docker build -t ish2api-proxy:latest .

docker run -d -p 8000:8000 --env-file ./.env --name ish2api-proxy-container --restart unless-stopped ish2api-proxy:latest



docker logs -f ish2api-proxy-container

