#!/bin/sh
# PULSE — Postgres init script: enable required extensions at first DB init.
# RESEARCH.md Pitfall #1 mandates a shell script (not .sql) per pgvector#355.
# Runs once when /var/lib/postgresql/data is empty (pgvector image inherits postgres entrypoint).

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";
  CREATE EXTENSION IF NOT EXISTS "vector";
EOSQL

echo "[pulse-db] extensions ready: uuid-ossp, pgcrypto, vector"
