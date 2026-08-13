#!/bin/sh
set -e
if [ -z "$DOMAIN" ]; then
  echo "ERROR: la variable de entorno DOMAIN no está definida." >&2
  echo "Define DOMAIN=tu-dominio.cl en tu .env antes de levantar nginx." >&2
  exit 1
fi
envsubst '${DOMAIN}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf
