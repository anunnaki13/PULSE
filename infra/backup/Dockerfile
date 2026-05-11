# PULSE — backup sidecar.
# Bundles pg_dump + psql (postgres:16-alpine), dcron (Alpine's stable cron), and rsync (NAS push).
# W-08 fix (Iteration 2 / CONTEXT.md Claude's Discretion): dcron is the chosen cron daemon
# for Alpine here (rather than the busybox suid variant, which has had stability issues).
# Entrypoint installs the crontab and runs crond in foreground so the container stays up.

FROM postgres:16-alpine

# rsync is required for the weekly NAS push (CONSTR-backup);
# dcron provides the cron daemon that drives both 02:00 backup and 03:00 Sunday rsync.
RUN apk add --no-cache rsync dcron

COPY scripts/ /scripts/
RUN chmod 0755 /scripts/*.sh

# Healthcheck via the presence of crond process is not configured here — the
# compose-level service healthcheck (if any) is owned by docker-compose.yml.

ENTRYPOINT ["/scripts/run-cron.sh"]
