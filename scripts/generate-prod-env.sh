#!/usr/bin/env bash
# Generate a production-ready PULSE env file without printing secret values.

set -euo pipefail

OUTPUT="${OUTPUT:-.env.production.generated}"
APP_BASE_URL="${APP_BASE_URL:-https://pulse.tenayan.local}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
FORCE="${FORCE:-false}"

if [ -f "$OUTPUT" ] && [ "$FORCE" != "true" ]; then
  echo "$OUTPUT already exists. Re-run with FORCE=true to overwrite." >&2
  exit 2
fi

secret() {
  python3 - <<'PY'
import base64
import os

print(base64.urlsafe_b64encode(os.urandom(48)).decode().rstrip("="))
PY
}

long_secret() {
  python3 - <<'PY'
import base64
import os

print(base64.urlsafe_b64encode(os.urandom(64)).decode().rstrip("="))
PY
}

APP_SECRET_KEY="$(long_secret)"
JWT_SECRET_KEY="$(long_secret)"
POSTGRES_PASSWORD="$(secret)"
INITIAL_ADMIN_PASSWORD="$(secret)"

cat > "$OUTPUT" <<EOF
# PULSE production env generated $(date -Iseconds)
# Keep this file outside Git. Review every value before deployment.

APP_SECRET_KEY=$APP_SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=60
JWT_REFRESH_TTL_DAYS=14

POSTGRES_HOST=pulse-db
POSTGRES_PORT=5432
POSTGRES_DB=pulse
POSTGRES_USER=pulse
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

REDIS_URL=redis://pulse-redis:6379/0

APP_BASE_URL=$APP_BASE_URL
APP_HOST_PORT=3399

OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_ROUTINE_MODEL=google/gemini-2.5-flash
OPENROUTER_COMPLEX_MODEL=anthropic/claude-sonnet-4
OPENROUTER_TIMEOUT_SECONDS=20
AI_MOCK_MODE=false
AI_MONTHLY_BUDGET_USD=5

BACKUP_DIR=/var/backups/pulse
BACKUP_RETAIN_DAYS=30
NAS_DEST=/mnt/nas/pulse-backups

INITIAL_ADMIN_EMAIL=admin@pulse.tenayan.local
INITIAL_ADMIN_PASSWORD=$INITIAL_ADMIN_PASSWORD
EOF

chmod 0600 "$OUTPUT"
echo "Generated $OUTPUT with strong local secrets. OpenRouter key present: $([ -n "$OPENROUTER_API_KEY" ] && echo true || echo false)"
echo "Next: review values, copy to .env on the production host, then run ./scripts/dev.sh prod-check."
