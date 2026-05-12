#!/usr/bin/env bash
# PULSE production smoke test.
# Required env: BASE_URL, EMAIL, PASSWORD
# Optional env: PERIODE_ID

set -euo pipefail

BASE_URL="${BASE_URL:-}"
EMAIL="${EMAIL:-}"
PASSWORD="${PASSWORD:-}"
PERIODE_ID="${PERIODE_ID:-}"

fail() {
  echo "prod-smoke: $1" >&2
  exit 1
}

[ -n "$BASE_URL" ] || fail "BASE_URL is required"
[ -n "$EMAIL" ] || fail "EMAIL is required"
[ -n "$PASSWORD" ] || fail "PASSWORD is required"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

health_code="$(curl -sS -o "$tmp_dir/health.json" -w '%{http_code}' "$BASE_URL/api/v1/health")"
[ "$health_code" = "200" ] || fail "/api/v1/health returned $health_code"

login_code="$(curl -sS -o "$tmp_dir/login.json" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  "$BASE_URL/api/v1/auth/login")"
[ "$login_code" = "200" ] || fail "/api/v1/auth/login returned $login_code"

access_token="$(python3 - <<'PY' "$tmp_dir/login.json"
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    data = json.load(fh)
print(data["access_token"])
PY
)"

auth_header="Authorization: Bearer $access_token"

me_code="$(curl -sS -o "$tmp_dir/me.json" -w '%{http_code}' -H "$auth_header" "$BASE_URL/api/v1/auth/me")"
[ "$me_code" = "200" ] || fail "/api/v1/auth/me returned $me_code"

detail_code="$(curl -sS -o "$tmp_dir/health-detail.json" -w '%{http_code}' -H "$auth_header" "$BASE_URL/api/v1/health/detail")"
[ "$detail_code" = "200" ] || fail "/api/v1/health/detail returned $detail_code"

ai_code="$(curl -sS -o "$tmp_dir/ai-status.json" -w '%{http_code}' -H "$auth_header" "$BASE_URL/api/v1/ai/status")"
[ "$ai_code" = "200" ] || fail "/api/v1/ai/status returned $ai_code"

if [ -n "$PERIODE_ID" ]; then
  dashboard_code="$(curl -sS -o "$tmp_dir/dashboard.json" -w '%{http_code}' -H "$auth_header" \
    "$BASE_URL/api/v1/dashboard/executive?periode_id=$PERIODE_ID")"
  [ "$dashboard_code" = "200" ] || fail "/api/v1/dashboard/executive returned $dashboard_code"

  pdf_code="$(curl -sS -L -o "$tmp_dir/nko.pdf" -w '%{http_code}' -H "$auth_header" \
    "$BASE_URL/api/v1/reports/nko-semester?periode_id=$PERIODE_ID&format=pdf")"
  [ "$pdf_code" = "200" ] || fail "/api/v1/reports/nko-semester returned $pdf_code"
  [ -s "$tmp_dir/nko.pdf" ] || fail "PDF export is empty"
fi

python3 - <<'PY' "$tmp_dir/me.json" "$tmp_dir/health-detail.json" "$tmp_dir/ai-status.json" "$PERIODE_ID" "$tmp_dir/dashboard.json" "$tmp_dir/nko.pdf"
import json
import os
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    me = json.load(fh)
with open(sys.argv[2], "r", encoding="utf-8") as fh:
    detail = json.load(fh)
with open(sys.argv[3], "r", encoding="utf-8") as fh:
    ai = json.load(fh)

print("PULSE production smoke")
print(f"user={me['email']}")
print(f"health_detail_status={detail['status']}")
print(f"ai_mode={ai['mode']}")

periode_id = sys.argv[4]
dashboard_path = sys.argv[5]
pdf_path = sys.argv[6]
if periode_id:
    with open(dashboard_path, "r", encoding="utf-8") as fh:
        dashboard = json.load(fh)
    print(f"periode_id={periode_id}")
    print(f"dashboard_nko={dashboard['snapshot']['nko_total']}")
    print(f"report_pdf_bytes={os.path.getsize(pdf_path)}")
PY
