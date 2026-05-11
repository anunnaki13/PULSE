# PULSE — public-facing reverse proxy.
# This is the ONLY service that publishes a host port (`${APP_HOST_PORT:-3399}:80`).
# Owns: security headers, rate-limit zones, CSRF passthrough, /ws upgrade, /api proxy.

FROM nginx:1.30-alpine

# Top-level nginx config.
COPY nginx.conf /etc/nginx/nginx.conf

# Server blocks + shared proxy include.
COPY conf.d/ /etc/nginx/conf.d/

# Drop the default vhost shipped by the base image (defensive — our nginx.conf
# already replaces it, but a stale default.conf in /etc/nginx/conf.d/ would still load).
RUN rm -f /etc/nginx/conf.d/default.conf || true

EXPOSE 80

# wget is part of busybox in nginx:alpine — used by the compose healthcheck.
CMD ["nginx", "-g", "daemon off;"]
