#!/usr/bin/env bash
# Apply the recommended PULSE UFW firewall policy on the production VPS.
#
# Usage:
#   sudo APP_PORT_MODE=https ./infra/production/apply-firewall.sh
#   sudo APP_PORT_MODE=direct-3399 ./infra/production/apply-firewall.sh

set -euo pipefail

MODE="${APP_PORT_MODE:-https}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root, for example: sudo APP_PORT_MODE=https $0" >&2
  exit 2
fi

if ! command -v ufw >/dev/null 2>&1; then
  echo "ufw is not installed" >&2
  exit 2
fi

ufw allow 22/tcp

case "$MODE" in
  https)
    ufw allow 443/tcp
    ufw deny 3399/tcp || true
    ;;
  direct-3399)
    ufw allow 3399/tcp
    ;;
  *)
    echo "APP_PORT_MODE must be https or direct-3399" >&2
    exit 2
    ;;
esac

ufw --force enable
ufw status verbose
