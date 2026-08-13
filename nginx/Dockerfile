FROM nginx:1.27-alpine

COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template

# La imagen base de nginx ejecuta automáticamente cualquier script en
# /docker-entrypoint.d/ antes de arrancar; usamos envsubst para sustituir
# ${DOMAIN} en el template y generar el nginx.conf real en cada arranque
# del contenedor (así el mismo build sirve para cualquier dominio, solo
# cambia la variable de entorno).
COPY docker-entrypoint-envsubst.sh /docker-entrypoint.d/40-envsubst-domain.sh
RUN chmod +x /docker-entrypoint.d/40-envsubst-domain.sh

EXPOSE 80 443
