# Verification record — 2026-10-18

Verified locally on Windows with a clean Python 3.13 virtual environment and the pinned lightweight backend requirements.

- Backend: **121 passed, 3 skipped**. Two skips are explicitly optional live TensorFlow inference; one is an existing conditional test. Three warnings concern the legacy UTC timestamp API.
- Frontend: **72 passed** across 18 files. React Router future-option warnings and some existing test-provider background network warnings remain; Vitest reports no failing tests.
- Production Vite build succeeds. Largest chart chunk is 395.47 kB before gzip (107.56 kB gzip), below Vite's default chunk warning threshold.
- Live local smoke checks: `/ready`, all five domain dashboard APIs, executive KPIs and `/executive` return 200. A missing asset returns 404 instead of HTML.
- Authenticated cross-domain SSE investigation returns a terminal `done` event and explicitly identifies its provider as `mock`. One warm local run took 0.51 seconds. This is a local measurement, not a hosted performance guarantee.
- Browser sign-in, executive data rendering, workspace navigation and investigation completion were checked against the production build.
- Regression coverage includes zero health scores, disabled TensorFlow loading, commit-triggered cache invalidation, scoped security event windows, blank optional cost fields, anonymous mutation rejection, temporary auth outages, premature SSE termination, unmount cancellation and building-switch cancellation.

Remote Render/Neon deployment and PostgreSQL behavior still require connected hosting accounts and live verification. No new public URL is verified yet. Local checks do not establish remote availability or free-tier memory capacity.
