#!/usr/bin/env bash
# PULSE production readiness checker.
# Validates go-live gates without printing secret values.

set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"
SKIP_DOCKER="${SKIP_DOCKER:-false}"
failures=()
warnings=()

fail() { failures+=("$1"); }
warn() { warnings+=("$1"); }

env_get() {
  local key="$1"
  if [ ! -f "$ENV_FILE" ]; then
    return 1
  fi
  awk -F= -v key="$key" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' "$ENV_FILE"
}

test_secret() {
  local name="$1"
  local min_len="${2:-32}"
  local value
  value="$(env_get "$name" || true)"
  if [ -z "$value" ]; then
    fail "$name is missing"
    return
  fi
  if [ "${#value}" -lt "$min_len" ]; then
    fail "$name must be at least $min_len characters"
  fi
  if printf '%s' "$value" | grep -Eiq 'replace|change|dev|default|password|pulse-.*-dev'; then
    fail "$name still looks like a placeholder or dev secret"
  fi
}

if [ ! -f "$ENV_FILE" ]; then
  fail "Missing env file: $ENV_FILE"
else
  test_secret "APP_SECRET_KEY"
  test_secret "JWT_SECRET_KEY"
  test_secret "POSTGRES_PASSWORD"
  test_secret "INITIAL_ADMIN_PASSWORD"

  [ -n "$(env_get OPENROUTER_API_KEY || true)" ] || fail "OPENROUTER_API_KEY is missing"
  [ "$(env_get AI_MOCK_MODE || true)" = "false" ] || fail "AI_MOCK_MODE must be false for production"
  printf '%s' "$(env_get APP_BASE_URL || true)" | grep -Eq '^https://' || fail "APP_BASE_URL must use https:// in production"
fi

[ -f infra/production/host-nginx-pulse.conf ] || fail "Missing host nginx TLS template"
[ -f infra/production/apply-firewall.sh ] || fail "Missing production firewall script"
[ -f infra/production/uptimerobot-monitor.example.json ] || fail "Missing external monitor example"

if [ "$SKIP_DOCKER" != "true" ]; then
  docker compose -f docker-compose.yml config --quiet || fail "docker compose config failed"

  db_ports="$(docker inspect pulse-db --format '{{json .NetworkSettings.Ports}}' 2>/dev/null || true)"
  if [ -n "$db_ports" ] && ! printf '%s' "$db_ports" | grep -q '"5432/tcp":null'; then
    fail "pulse-db appears to expose port 5432 to the host"
  fi

  nginx_ports="$(docker inspect pulse-nginx --format '{{json .NetworkSettings.Ports}}' 2>/dev/null || true)"
  if [ -n "$nginx_ports" ] && ! printf '%s' "$nginx_ports" | grep -q '"80/tcp"'; then
    fail "pulse-nginx does not expose the app port"
  fi

  log_config="$(docker inspect pulse-nginx --format '{{json .HostConfig.LogConfig}}' 2>/dev/null || true)"
  if [ -n "$log_config" ] && ! printf '%s' "$log_config" | grep -q '"max-size":"10m"'; then
    warn "Docker log rotation is not visible on pulse-nginx; recreate stack with docker compose -f docker-compose.yml up -d --wait"
  fi
fi

echo "PULSE production readiness"
if [ "${#warnings[@]}" -gt 0 ]; then
  echo "Warnings:"
  printf '  - %s\n' "${warnings[@]}"
fi
if [ "${#failures[@]}" -gt 0 ]; then
  echo "Failures:"
  printf '  - %s\n' "${failures[@]}"
  exit 1
fi

echo "PASS: production readiness checks passed"
