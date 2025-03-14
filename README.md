# ImmichKiosk webhook server

1. Copy or download the compose file from [here](https://github.com/damongolding/immich-kiosk-webhook-server/blob/main/docker-compose.yaml).


2. Create a .env file with the following content:

```env
IMMICH_URL=http://IP:2283
IMMICH_API_KEY=api_key
ALBUM_ID=album_id
SECRET=secret_key
```

3. Run the server with the following command:

```bash
docker compose up -d
```
