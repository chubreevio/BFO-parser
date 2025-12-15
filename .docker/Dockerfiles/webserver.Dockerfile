FROM nginx:1.23.0-alpine
ARG APP_HOSTNAME

COPY .docker/nginx/nginx.conf /tmp/nginx.conf
RUN envsubst '${APP_HOSTNAME}' < /tmp/nginx.conf > /etc/nginx/conf.d/tracking.conf

EXPOSE 80
EXPOSE 443

STOPSIGNAL SIGTERM
