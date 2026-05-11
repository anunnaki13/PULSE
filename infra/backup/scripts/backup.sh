#!/bin/sh
# PULSE — backup.sh.
# Dumps PGDATABASE on PGHOST to BACKUP_DIR/pulse-<UTC-timestamp>.sql.gz,
# then prunes anything older than RETAIN_DAYS (default 30).
# Required env: BACKUP_DIR, PGHOST, PGUSER, PGDATABASE. PGPASSWORD via env_file.

set -eu

: "${BACKUP_DIR:?BACKUP_DIR must be set}"
: "${PGHOST:?PGHOST must be set}"
: "${PGUSER:?PGUSER must be set}"
: "${PGDATABASE:?PGDATABASE must be set}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="${BACKUP_DIR}/pulse-${TS}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[backup] $(date -u +%FT%TZ) writing ${OUT}"

# --no-owner + --clean + --if-exists makes the dump portable: it does not
# encode the original role, and restore drops & recreates objects cleanly.
pg_dump \
    --no-owner \
    --clean \
    --if-exists \
    -h "${PGHOST}" \
    -U "${PGUSER}" \
    "${PGDATABASE}" \
  | gzip > "${OUT}"

echo "[backup] retaining ${RETAIN_DAYS:-30} days under ${BACKUP_DIR}"
find "${BACKUP_DIR}" -maxdepth 1 -name 'pulse-*.sql.gz' -mtime "+${RETAIN_DAYS:-30}" -delete

echo "[backup] current contents (last 10):"
ls -lh "${BACKUP_DIR}" | tail -10
