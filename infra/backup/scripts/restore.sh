#!/bin/sh
# PULSE — restore.sh. Accepts a backup filename (absolute or relative to BACKUP_DIR),
# gunzip-pipes it into psql. CONSTR-backup acceptance: "pipe into psql, accept backup filename".
#
# Usage:
#   /scripts/restore.sh pulse-20260511T020000Z.sql.gz   # relative
#   /scripts/restore.sh /backups/pulse-...sql.gz        # absolute
# Required env: BACKUP_DIR (when relative path), PGHOST, PGUSER, PGDATABASE, PGPASSWORD.

set -eu

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <backup-file>" >&2
  exit 2
fi

FILE="$1"
case "$FILE" in
  /*) ABS="$FILE" ;;
  *)  ABS="${BACKUP_DIR:?BACKUP_DIR must be set for relative paths}/$FILE" ;;
esac

if [ ! -f "$ABS" ]; then
  echo "[restore] not found: $ABS" >&2
  exit 2
fi

: "${PGHOST:?PGHOST must be set}"
: "${PGUSER:?PGUSER must be set}"
: "${PGDATABASE:?PGDATABASE must be set}"

echo "[restore] loading $ABS into $PGDATABASE on $PGHOST"
gunzip -c "$ABS" \
  | psql \
      -v ON_ERROR_STOP=1 \
      -h "$PGHOST" \
      -U "$PGUSER" \
      -d "$PGDATABASE"

echo "[restore] done."
