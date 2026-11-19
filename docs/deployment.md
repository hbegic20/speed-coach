# Deploying SpeedCoach

```
Browser ──► Vercel (web, fra1) ──server-side──► Railway: api ──► Railway Postgres
                                                       │      └─► Railway Redis
                                                       └ jobs ─► Railway: worker ──► PageSpeed, Gemini
```

The web app never calls the API from the browser, so the API needs no CORS setup. API and worker run the same Docker image (`api/Dockerfile`); only the start command differs.

## 1. Secrets to prepare

| Secret | How to get it |
| --- | --- |
| `PAGESPEED_API_KEY` | Google Cloud Console → enable **PageSpeed Insights API** → Credentials → API key. Restrict it to that API. |
| `GEMINI_API_KEY` | Google AI Studio → API keys. |
| `WEB_PROXY_SECRET` | Generate once: `openssl rand -hex 32`. The **same value** goes on the API and on Vercel. |

## 2. Railway

Create one project in an EU region (for example `europe-west4`), then add:

1. **Postgres** database (template).
2. **Redis** database (template).
3. **api** service from this GitHub repo:
   - Settings → Source → Root directory: `/api`
   - Settings → Config-as-code → Railway config file: `/api/railway.json`
   - Settings → Networking → Generate a public domain.
4. **worker** service from the same repo:
   - Root directory: `/api`
   - Railway config file: `/api/railway.worker.json`
   - No public domain.

`railway.json` runs `alembic upgrade head` before every API deploy, so a failing migration stops the deploy instead of starting an app against the wrong schema. It also health-checks `/health`, which checks the database connection. Both services only redeploy when files under `api/` change.

### Variables

Set these on **both** the `api` and `worker` services (shared variables work well):

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (the plain `postgresql://` URL is converted to the async driver automatically) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `PAGESPEED_API_KEY` | from step 1 |
| `GEMINI_API_KEY` | from step 1 |
| `WEB_PROXY_SECRET` | from step 1 (needed by `api`; harmless on `worker`) |

Optional, with defaults:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Model for fix suggestions |
| `PAGESPEED_TIMEOUT_SECONDS` | `90` | One PageSpeed run |
| `PAGESPEED_CACHE_TTL_SECONDS` | `900` | Reuse results per URL and device |
| `PAGE_FETCH_TIMEOUT_SECONDS` | `10` | Platform detection fetch |
| `GEMINI_TIMEOUT_SECONDS` | `60` | One Gemini call |
| `AUDIT_BURST_LIMIT` / `AUDIT_BURST_WINDOW_SECONDS` | `5` / `600` | Audits per visitor per window |
| `AUDIT_DAILY_LIMIT` | `30` | Audits per visitor per day |
| `AUDIT_GLOBAL_DAILY_LIMIT` | `500` | Audits per day for everyone together |
| `SITE_HOURLY_LIMIT` | `30` | Sites tracked per visitor per hour |
| `SCHEDULED_CHECKS_ENABLED` | `true` | Weekly re-check of every tracked site |
| `SCHEDULED_CHECK_MIN_INTERVAL_HOURS` | `144` | Skip sites checked more recently than this |
| `SCHEDULED_CHECK_SPACING_SECONDS` | `20` | Gap between scheduled audits, to spread quota use |

Railway sets `PORT`; the image listens on it.

## 3. Vercel

1. Import the repo, set **Root directory** to `web`. The framework (Next.js) and pnpm are detected.
2. Environment variables (Production and Preview):

| Variable | Value |
| --- | --- |
| `API_URL` | the API's public Railway URL, for example `https://speedcoach-api.up.railway.app` |
| `WEB_PROXY_SECRET` | the same value as on Railway |

`web/vercel.json` pins functions to `fra1` (Frankfurt), close to Bosnian visitors and to an EU Railway region.

## 4. After the first deploy

1. `curl https://<api-domain>/health` returns `{"status":"ok"}`.
2. Open the Vercel URL, run an audit on a real site and wait for the report.
3. Railway → worker → Logs shows `run_audit(...)` finishing.
4. Run Lighthouse against the Vercel URL; every category should be 95 or higher.

## Notes

- **Weekly checks.** The worker re-checks every tracked site on Mondays at 06:00 Europe/Sarajevo, skipping sites checked in the last 6 days, in the language of each site's last check. Each check costs two PageSpeed runs and one Gemini call, so 200 tracked sites use about 400 PageSpeed requests and 200 Gemini calls every Monday. With 20 s spacing, 200 sites take a little over an hour to queue through. Scheduled checks are not counted against visitor rate limits or the daily total. Set `SCHEDULED_CHECKS_ENABLED=false` on the worker to pause them. The job is unique, so extra worker replicas don't run it twice.

- **Rate limits and real visitor IPs.** Visitors are identified by the IP the web app forwards together with `WEB_PROXY_SECRET`. If the secret is missing or differs between Vercel and Railway, every visitor shares one bucket and the limits trip quickly. Direct API callers are counted by the address Railway's proxy connects from; the API does not trust `X-Forwarded-For`, which a caller could forge.
- **Rollbacks.** Migrations have working downgrades, but roll back code first, then run `alembic downgrade -1` from the api service shell only if the schema itself must go back.
- **Local production check.** `docker build -t speedcoach-api api` and run it with the same variables; `docker run ... speedcoach-api arq app.worker.WorkerSettings` starts the worker.
