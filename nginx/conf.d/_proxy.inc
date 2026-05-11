# PULSE — shared proxy directives, included from every backend location block in pulse.conf.
# Underscore prefix keeps this file from matching `*.conf` in nginx.conf's include glob,
# so it is only ever pulled in via explicit `include` from a sibling vhost.

proxy_http_version 1.1;
proxy_set_header   Host              $host;
proxy_set_header   X-Real-IP         $remote_addr;
proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header   X-Forwarded-Proto $scheme;

proxy_connect_timeout 5s;
proxy_send_timeout    60s;
proxy_read_timeout    60s;
