# FacilityOps reliability implementation plan

> Execute inline using superpowers:executing-plans, as requested by the user.

**Goal:** Deliver a verified single-origin application and accurate interview guide.
**Architecture:** Preserve React/Vite, FastAPI, SQLAlchemy and the five domain agents. Correct integration boundaries and optional-runtime behavior before polishing UI.
**Tech stack:** React 18, Vite 5, Python, FastAPI, scikit-learn, optional TensorFlow.
**Spec:** ../specs/2026-10-18-facilityops-reliability-design.md

## Constraints and review focus
Free hosting only; preserve core workflows; disclose optional inference and persistence limits. Test absent build-time URL configuration, transient authentication failures, replacement/unmounted streams, disabled TensorFlow, zero health scores, unknown assets/routes, and clean-database startup.

## Tasks
1. Test isolation and runtime: add backend/tests/conftest.py with a temporary database and deterministic demo settings before app import. Regression tests cover disabled CNN inference and maintenance score zero. Keep full-runtime tests conditional on explicit TensorFlow availability, with core fallback assertions. Fix confirmed production defects and rerun backend tests.
2. Browser integration: centralize API_BASE_URL in frontend/src/services/apiConfig.js, default `/api`; test real Axios adapter requests. Add AuthContext tests for 401 versus transient failures; implement retry and bounded requests. Add stream-hook tests for cancellation and interrupted streams; guard stale updates and clean up on unmount.
3. Server delivery: add tests for readiness state, missing assets/API routes, and SPA routes. Isolate startup ingestion by domain and report readiness. Keep internal failures in server logs. Separate lightweight hosting requirements from optional TensorFlow requirements.
4. UI: fix shell responsiveness, labels and copy; add unknown-route recovery and reduced-motion settings. Verify production build and browser desktop/mobile flows; regression-test meaningful navigation behavior.
5. Documentation and deployment: inspect source and model artifacts; write architecture/interview guide and operational runbook. Run full suites, build, live API smoke tests, then deploy through connected Render with durable free database if available. Verify remote behavior before declaring completion.

## Execution ledger
- Baseline: frontend 64 passed; Python 3.13 collection blocked by missing bcrypt; Python 3.14 core run 94 passed, 10 failed, 1 skipped. Eight failures depend on existing admin credentials; two require optional TensorFlow.
- Ruling: work in the user's supplied project copy, preserving its installed dependencies and local files; use a dedicated branch. The user explicitly approved implementation here. No extra worktree needed for a single inline implementer.
- Ruling: the user has reviewed the written spec and explicitly requested inline implementation; proceed without repeating the same authorization question.

- Verified: backend 121 passed / 3 skipped, frontend 72 passed, production build succeeded. See docs/VERIFICATION.md.
- Review fixes: authenticated dataset/investigation actions; scoped security drift; cancel/reset streams on building switches; sanitize blank cost fields.
- Deployment pending: Render and Neon plugins still report installed=false. Prepared Docker, Blueprint, runbook and interview guide; no new public link claimed.
