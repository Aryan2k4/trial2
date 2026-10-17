# FacilityOps reliability and deployment design

## Approved intent
Preserve the existing React, FastAPI, and trained ML functionality; repair the application end to end; improve usability and responsiveness; deploy frontend and backend at one public URL using free hosting; provide code-grounded interview preparation. The user approved this scope on 2026-10-18 and accepts cold starts.

## Architecture
Retain the existing domain agents and SQLAlchemy models. FastAPI serves the Vite production build and all `/api` routes. Browser requests default to the relative `/api` path, including authentication and streamed investigations. Vite proxies this path during development. A single configuration module prevents divergent URLs.

Retain Energy, Maintenance, Occupancy, Security, Cost, and Executive dashboards, authentication, dataset operations, forecasts, investigations, handoffs, negotiation, and model diagnostics. Optional TensorFlow models must report availability honestly. The tree-based maintenance model and core occupancy classifier remain functional when TensorFlow is disabled. Do not substitute fabricated predictions for missing inference.

## Reliability
Distinguish service liveness from completion of seed-data ingestion. Failed domain ingestion must be logged and exposed as readiness information without silently preventing other domains from initializing. Do not expose exception internals to public clients. Missing API routes and static assets return proper 404 responses; known client routes load the SPA.

Authentication keeps a valid stored token during transient network/server failures and offers retry. Only an invalid/expired token clears the session. Bound network waits. Agent streams cancel on navigation and replacement, ignore stale responses, and expose interrupted streams as incomplete rather than successful. Preserve backend authorization checks.

## UI
Retain the visual identity and dashboard-specific charts. Make the app shell usable at mobile widths without a full-height sidebar preceding the page. Add accessible labels, visible focus, reduced-motion support, a useful unknown-route state, and accurate agent-count/status copy. Improve loading, retry, and unavailable-model states where diagnostics find failures.

## Hosting
Use a free Render web service with one public origin, configured secrets, and the existing Docker build after verification. Render connection is required to manage deployment. Free Render PostgreSQL expires after 30 days; use an existing durable compatible database or a verified free external PostgreSQL service if available. A reseeded ephemeral demo must be clearly disclosed and cannot be represented as durable storage. No paid resources without user authorization. TensorFlow runtime must remain optional for small instances; preserve the full local runtime option.

## Validation
Run frontend and backend suites, add behavioral regression coverage for confirmed failures, build production assets, then exercise the running service from signup/login through all six dashboards and supported mutations. Check desktop/mobile navigation and network errors. Verify the deployed page, API health, and representative authenticated actions before giving a final working URL. Document any infrastructure or optional-model limitation explicitly.

## Interview deliverable
Document actual request flow, database entities, domain responsibilities, ML artifacts/metrics/provenance, rules versus ML versus LLM orchestration, tool calling and handoffs, authentication, streaming, caching, deployment tradeoffs, known limitations, and common interview questions. Trace statements to source files. Do not repeat README performance claims without checking model metrics and code.

## Alternatives considered
A complete rewrite offers uniformity but risks dropping trained models and domain workflows. A static frontend rebuild cannot provide the Python inference and write APIs. Targeted repair preserves the strongest project evidence while addressing deployment and UX failures.
