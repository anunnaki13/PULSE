---
status: ready-for-operator
phase: 06-stream-coverage-hcr-golive
plan: 05
updated_at: "2026-05-12T14:55:00.000+07:00"
---

# Phase 06 Go-Live Runbook

## 1. Generate Production Env

On the production host:

```bash
cd /opt/pulse
OUTPUT=.env.production.generated APP_BASE_URL=https://pulse.tenayan.local ./scripts/generate-prod-env.sh
```

On a Windows operator machine:

```powershell
./scripts/generate-prod-env.ps1 -Output .env.production.generated -AppBaseUrl https://pulse.tenayan.local
```

Edit `.env.production.generated` and set:

- `OPENROUTER_API_KEY`
- `NAS_DEST` if off-site backup target differs
- `INITIAL_ADMIN_EMAIL` if the first admin email must differ

Then install it:

```bash
cp .env.production.generated .env
chmod 0600 .env
```

Do not commit `.env` or `.env.production.generated`.

## 2. Start Production Compose

Use the production-shape compose file only:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d --wait
docker compose -f docker-compose.yml ps
```

Do not use `docker-compose.override.yml` on the production VPS; that file enables dev reload/HMR.

## 3. Seed and Verify Data

```bash
docker compose -f docker-compose.yml exec pulse-backend python -m app.seed
docker compose -f docker-compose.yml exec pulse-db psql -U pulse -d pulse -At -c "select count(*) from pedoman_chunks;"
```

Expected Pedoman chunks for the local seeded corpus: `5`.

## 4. Firewall

If serving directly on port 3399:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 3399/tcp
sudo ufw enable
sudo ufw status verbose
```

If terminating TLS on standard HTTPS:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw deny 3399/tcp
sudo ufw enable
sudo ufw status verbose
```

Postgres must not be exposed publicly. Verify:

```bash
docker inspect pulse-db --format '{{json .NetworkSettings.Ports}}'
```

Expected: `"5432/tcp":null`.

## 5. SSL

Recommended production pattern:

- Keep app compose bound to internal or host-local HTTP.
- Terminate TLS at a host reverse proxy or managed edge.
- Forward only to PULSE Nginx.

For host Nginx + Certbot:

```bash
sudo certbot --nginx -d pulse.tenayan.local
sudo certbot renew --dry-run
```

Then confirm:

```bash
curl -fsS https://pulse.tenayan.local/api/v1/health
```

## 6. Backup and Restore Drill

```bash
docker compose -f docker-compose.yml exec pulse-backup /scripts/backup.sh
LATEST=$(docker exec pulse-backup sh -c "ls -1t /backups/pulse-*.sql.gz | head -1")
docker exec pulse-db dropdb -U pulse --if-exists pulse_restore_probe
docker exec pulse-db createdb -U pulse pulse_restore_probe
docker exec -e PGDATABASE=pulse_restore_probe pulse-backup /scripts/restore.sh "$LATEST"
docker exec pulse-db psql -U pulse -d pulse_restore_probe -At -c "select count(*) from information_schema.tables where table_schema = 'public';"
docker exec pulse-db dropdb -U pulse --if-exists pulse_restore_probe
```

Expected restored public tables: at least `25`.

## 7. OpenRouter

Verify production AI mode:

```bash
curl -fsS -H "Authorization: Bearer <TOKEN>" https://pulse.tenayan.local/api/v1/ai/status
```

Expected:

- `mode=openrouter`
- `available=true`
- `AI_MOCK_MODE=false` in `.env`

Mock fallback code remains present, but production must not run in mock mode.

## 8. External Monitoring

Configure an external monitor against:

- `https://pulse.tenayan.local/api/v1/health` for public liveness
- Optional authenticated internal check for `/api/v1/health/detail`

Alert on:

- HTTP non-2xx
- TLS expiry
- response time > 5 seconds
- repeated container restart events

## 9. Nginx Hardening Check

Validate the shipping nginx config before go-live:

```bash
docker compose -f docker-compose.yml exec pulse-nginx nginx -t
```

The app nginx now includes:

- API rate limiting
- AI endpoint rate limiting
- login brute-force throttling
- WebSocket connection cap on `/ws/`

## 10. Post-Deploy Smoke

Run after `prod-check` passes and the target stack is reachable:

```bash
BASE_URL=https://pulse.tenayan.local \
EMAIL=admin@pulse.tenayan.local \
PASSWORD='<admin-password>' \
PERIODE_ID='<periode-uuid>' \
./scripts/dev.sh prod-smoke
```

Windows:

```powershell
./scripts/dev.ps1 prod-smoke -BaseUrl https://pulse.tenayan.local -Email admin@pulse.tenayan.local -Password '<admin-password>' -PeriodeId '<periode-uuid>'
```

If `PERIODE_ID` is provided, the smoke also verifies:

- executive dashboard
- NKO PDF export

## 11. Final Gate

Run:

```bash
./scripts/dev.sh prod-check
```

or on Windows:

```powershell
./scripts/dev.ps1 prod-check
```

Phase 06 can be closed for go-live only after this command passes and the final business UAT is accepted.
