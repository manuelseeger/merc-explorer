FROM joseluisq/static-web-server:2.44.0-alpine

ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=80 \
    SERVER_ROOT=/home/sws/public \
    SERVER_COMPRESSION=true \
    SERVER_CACHE_CONTROL_HEADERS=false

COPY --chown=sws:sws index.html data.js healthz /home/sws/public/

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:80/healthz || exit 1
