#!/bin/sh
# PULSE — run-cron.sh. Entry point for the pulse-backup sidecar.
# Installs the locked crontab (CONSTR-backup: daily 02:00 backup, Sunday 03:00 rsync to NAS)
# then runs crond in the foreground so the container stays up and logs to stdout.

set -eu

# Default NAS destination if the env var is unset. Phase 1 acceptance is the local
# daily backup; rsync to NAS is best-effort (RESEARCH.md Assumption A7).
: "${NAS_DEST:=/mnt/nas/pulse-backups}"

# Cron in Alpine reads /etc/crontabs/<user>. crond runs jobs as that user.
# Note: cron does NOT expand shell variables in command lines, so we materialize
# NAS_DEST here (in the install shell) using a quoted heredoc to control expansion.
echo "[init] installing cron schedule (daily 02:00 backup, Sunday 03:00 rsync)"

# Ensure the directory exists (cron + log target).
mkdir -p /etc/crontabs /backups

# Build crontab: variables that cron should see (PATH + DB connection vars from env)
# must be set INSIDE the crontab too — crond's PATH defaults to /usr/bin:/bin, which
# would not find psql / pg_dump from the postgres alpine image without PATH.
cat > /etc/crontabs/root <<CRON
# PULSE backup schedule (locked: CONSTR-backup)
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/root
PGHOST=${PGHOST:-pulse-db}
PGUSER=${PGUSER:-pulse}
PGDATABASE=${PGDATABASE:-pulse}
PGPASSWORD=${PGPASSWORD:-}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETAIN_DAYS=${RETAIN_DAYS:-30}

# Daily pg_dump | gzip
0 2 * * * /scripts/backup.sh >> /backups/backup.log 2>&1

# Weekly rsync to NAS (Sunday 03:00). Best-effort — A7: NAS may not be reachable from inside Docker.
0 3 * * 0 rsync -a /backups/ ${NAS_DEST}/ >> /backups/rsync.log 2>&1
CRON

echo "[init] crontab installed:"
cat /etc/crontabs/root
echo "----"
# dcron 4.5 in the current postgres:16-alpine + Docker runc combo fails to
# call setpgid() under foreground modes (`crond -f -L /dev/stdout` or `-d`)
# with "setpgid: Operation not permitted", putting the container in a
# restart loop. Plan-07 Rule-3 (blocking) fix: run dcron in background mode
# (`-b`) — it daemonizes successfully, the cron schedule is active, and we
# keep the container alive by tailing the cron log. W-08 preserved (still
# dcron — verify via `crond -V` → "dillon's cron daemon 4.5").
echo "[init] starting crond -b (background, with tail-f log keep-alive)"
touch /backups/cron.log
crond -b -L /backups/cron.log
# Verify daemon is alive before entering tail.
sleep 1
if pgrep crond >/dev/null 2>&1; then
  echo "[init] crond daemonized OK (pid=$(pgrep crond))"
else
  echo "[init] FATAL crond failed to daemonize"
  exit 1
fi
# Keep PID 1 alive so docker compose sees a healthy long-running process.
exec tail -F /backups/cron.log /backups/backup.log /backups/rsync.log 2>/dev/null
