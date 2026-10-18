# FacilityOps runbook

## Local single-origin application (Windows)

After the first-time dependency setup below, run `./start.ps1` from the repository root. It rebuilds the frontend and starts the combined app using your `backend/.env`, including your chosen AI provider. Restart after changing environment settings.

Use Python 3.13 and Node 20 or newer. From the repository root:

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
$env:VITE_API_BASE_URL='/api'
npm run build
cd ../backend
$env:ENABLE_TENSORFLOW='false'
$env:AI_PROVIDER='mock'
../.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and create an account. React and `/api` share this address. The server detects `frontend/dist` locally; the Docker image uses `frontend_dist`. Initial data ingestion runs in the background. `/health` checks the process, while `/ready` returns 503 during loading and 200 once all five datasets are ready. SQLite is the local default. Existing local `.env` configuration is loaded without overwriting shell environment variables.

For hot-reload frontend development, run `npm run dev` in `frontend` and the API separately; Vite proxies `/api` to port 8000.

## Free deployment: Render + Neon

The major hosting plugin is **Render**. **Neon** supplies persistent PostgreSQL. Connect both accounts to deploy through the plugins. GitHub holds the source. Figma and Sites are not required for this Python application.

1. Create a Neon project on its free plan, close to Render's Singapore region where available. Use a pooled PostgreSQL connection URL with TLS. Keep it in the provider secret configuration, never in Git or interview documents.
2. Deploy this repository and the verified branch/commit as a Render **free Docker web service**, using the root `Dockerfile`. Set `DATABASE_URL` to the Neon connection URL, `AI_PROVIDER=mock`, `ENABLE_TENSORFLOW=false`, `OMP_NUM_THREADS=1`, and `OPENBLAS_NUM_THREADS=1`.
3. Set a randomly generated `JWT_SECRET_KEY`, a private `ADMIN_USERNAME`, and a strong `ADMIN_PASSWORD`. `render.yaml` contains the service settings and requests these secrets. The admin seed only creates a missing user; changing the environment password does not reset an existing database user.
4. Keep the health check `/health` so background ingestion can complete after the service starts. Verify `/ready`, all six dashboards, signup/login, authenticated investigation streaming, record add/delete, and a refresh of a nested frontend route before sharing the URL.
5. Publish only the Render service URL: it serves the frontend, API, assets, and `/docs`. No second frontend host is needed. Do not enable a paid plan without explicit approval.

Render free web services sleep after inactivity and may take about a minute to wake. Neon also scales to zero. Free quotas and terms can change; check [Render](https://render.com/docs/free) and [Neon](https://neon.com/pricing). Render's free PostgreSQL expires after 30 days, which is why this setup uses external PostgreSQL. Free hosting has no uptime guarantee.

## Model modes

The lightweight default runs the classical ML models and clearly labeled scripted investigations without an API key. It does not perform live LSTM/CNN inference. To run those optional models on a machine with sufficient memory, install `backend/requirements-deep-learning.txt`, set `ENABLE_TENSORFLOW=true`, and restart. Stored training metrics are historical evaluations, not proof that a live model ran.

For LLM-driven tool selection, configure a supported provider in `backend/app/core/config.py` and its API key in the hosting environment. Test provider status at `/api/system/ai-status`. Paid provider use is not required for the demo.

## Verification

```powershell
cd backend
../.venv/Scripts/python -m pytest -q
cd ../frontend
npm test -- --run
npm run build
```

Backend tests create an isolated temporary SQLite database and never intentionally use your working database. Two live TensorFlow tests are skipped in the lightweight mode; enable and install TensorFlow to run them. A separate historical conditional test can also skip. The test suite is not a PostgreSQL deployment test: verify the real hosted database separately.

## Operational boundaries and troubleshooting

- A failed login verification during a server outage preserves the browser token and offers retry. A genuine 401 clears it.
- An interrupted investigation reports failure instead of waiting forever. Changing building or leaving the page cancels browser consumption. Already committed work orders/alerts are not rolled back by cancellation; investigate existing records before repeating a run.
- All signed-up technicians can change the shared demo dataset. Read APIs intentionally remain public. Use only demonstration data. Private production use requires tenant permissions, signup policy, rate limits, audit logging, and backups.
- Analytics caches are invalidated after database commits within one process. Keep one Uvicorn worker for this deployment; multiple workers require shared cache revision/invalidation.
- If `/ready` is degraded, examine the failing domain's server log, database connectivity, and packaged CSV paths. Do not delete a database to resolve startup issues.
- Deploying with SQLite on Render loses changes when the ephemeral filesystem is replaced. Always supply the persistent PostgreSQL URL.
- Roll back application code to a known working commit through Render. Database data is independent; take provider backups/exports before destructive changes. This project uses `create_all` and an explicit index upgrade, not a full migration framework.

For architecture and interview preparation, read `INTERVIEW_GUIDE.md`, then use `SOURCE_MAP.md` to trace each endpoint to its implementation.
