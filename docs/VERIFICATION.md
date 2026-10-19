# Verification record — 2026-10-18

Verified locally on Windows with a clean Python 3.13 virtual environment and the pinned lightweight backend requirements.

- Backend: **125 passed, 3 skipped**. Two skips are explicitly optional live TensorFlow inference; one is an existing conditional test. Three warnings concern the legacy UTC timestamp API.
- Frontend: **72 passed** across 18 files. React Router future-option warnings and some existing test-provider background network warnings remain; Vitest reports no failing tests.
- Production Vite build succeeds. Largest chart chunk is 395.47 kB before gzip (107.56 kB gzip), below Vite's default chunk warning threshold.
- Live local smoke checks: `/ready`, all five domain dashboard APIs, executive KPIs and `/executive` return 200. A missing asset returns 404 instead of HTML.
- Authenticated cross-domain SSE investigation returns a terminal `done` event and explicitly identifies its provider as `mock`. One warm local run took 0.51 seconds. This is a local measurement, not a hosted performance guarantee.
- Browser sign-in, executive data rendering, workspace navigation and investigation completion were checked against the production build.
- Regression coverage includes zero health scores, disabled TensorFlow loading, commit-triggered cache invalidation, scoped security event windows, blank optional cost fields, anonymous mutation rejection, temporary auth outages, premature SSE termination, unmount cancellation and building-switch cancellation.

## Cloud verification — 2026-10-19

Deployed commit `b752067` to https://facilityops.onrender.com (React and FastAPI share this origin). Render reported a successful Docker deployment.

- `/health` returned 200. `/ready` initially returned 503 while ingestion ran, then returned 200 with all five domains ready.
- All five domain dashboard endpoints returned 200; executive KPIs returned 200 with no domain errors.
- Browser signup and automatic login succeeded; executive and energy dashboards rendered real API data.
- A live Groq energy investigation completed with five tool calls, a final synthesis and a maintenance-review handoff. Provider: `openai/gpt-oss-120b`.
- Initial overview aggregation is slow on the free instance, especially after writes invalidate analysis caches. Cold-start and warm-response times must not be conflated.
- **Persistence verified:** Render now uses Neon PostgreSQL (Singapore), project `odd-water-91115569`, branch `render-deployment`. Application schema `facilityops_app` contains 15 tables. A public signup returned 200, authenticated profile returned 200, and a separate direct SQL connection confirmed the same account exists in Neon. Energy ingestion contains 35,040 records; all five startup datasets report ready.
- Post-switch dashboard checks: energy, maintenance, occupancy, security, cost and executive KPIs all returned 200. First maintenance fetch took 19.47 seconds and security 7.52 seconds; this free instance is not a low-latency SLA.
- Post-switch Groq streaming reached five tools but hit the provider usage quota; the UI receives an explicit quota error. Earlier cloud runs completed successfully. Real AI remains dependent on the account's available quota.
- The existing unused Render PostgreSQL instance was left untouched. Previous temporary SQLite-only accounts were not migrated; create an account on the persistent deployment if needed.

The free deployment disables optional TensorFlow inference. Classical ML and Groq are enabled; Groq quota limits may still interrupt investigations.

Groq follow-up: real energy investigation completed with five tool calls and a final summary in 12.41 seconds locally. Prior run took 60.61 seconds. Four new regression tests cover duplicate summary requests, quota retry bounds, and prevention of mock-tool replay after a partially completed real investigation.
