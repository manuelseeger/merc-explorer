# A.I.M. Merc Explorer

A static Jagged Alliance 2 mercenary browser. Search and filter 67 profiles,
compare skills, statistics and costs, and inspect relationships.

`index.html` contains the interface, styles and app code. `data.js` contains
profile data and embedded PNG portraits. No external assets or runtime API are
required. `extract.py` and `sti.py` are source data tools, not server dependencies.

## Local test

Requires Docker with Compose.

```sh
docker compose -f compose.yaml config
docker compose -f compose.yaml -f compose.dev.yaml up --build --wait
curl --fail http://127.0.0.1:18080/healthz
curl --fail -o /dev/null http://127.0.0.1:18080/
curl --fail -o /dev/null http://127.0.0.1:18080/data.js
```

Open `http://127.0.0.1:18080` in a browser. Test search, filters and profile
selection. Stop the local test:

```sh
docker compose -f compose.yaml -f compose.dev.yaml down
```

## m3s package

`compose.yaml` builds the `web` service with nginx Alpine on internal port 80.
It has no host ports. Route m3s to service `web`, port `80`, health path
`/healthz`. This route returns HTTP 200 with plain text `ok`.
Docker and Compose healthchecks test the route. Only `compose.dev.yaml`
publishes a host port, bound to `127.0.0.1:18080`.
