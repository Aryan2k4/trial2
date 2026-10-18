# FacilityOps: architecture and interview preparation

This guide describes the checked-in implementation, not an imagined production system. Metrics below come from `backend/ml_models/**/model_metrics.json`; they are saved training results, not a new training run. See `SOURCE_MAP.md` for an automatically generated route, model, and function inventory.

## Your 60-second explanation

“FacilityOps is a facility-operations decision-support application. A React dashboard calls a FastAPI backend that combines five domains: energy, maintenance, occupancy, security, and cost. Each domain separates data ingestion, analytics, recommendations, and optional LLM investigation. Trained models produce forecasts or anomaly scores; deterministic rules convert those into operational suggestions. An investigation can call real tools and create work orders or alerts in the database. The executive view aggregates the five domains. I can run the core application without an LLM key, but that mode uses explicitly labeled scripted investigations. The frontend and API are served from one origin.”

Only claim work you actually did. Distinguish original team contributions from repairs made with coding-agent assistance. Be ready to explain and reproduce each decision rather than memorize this paragraph.

## Request flow

1. `frontend/src/main.jsx` mounts `App.jsx`. Theme, authentication, building selection, and toast contexts wrap the routes.
2. `ProtectedRoute.jsx` checks the frontend authentication state. A stored JWT is verified through `/api/auth/me`. This frontend gate is not a substitute for API authorization.
3. A dashboard calls a service module. The shared Axios client in `services/energyService.js` attaches the current bearer token. `services/apiConfig.js` defaults to `/api`, so the same build can use FastAPI’s origin. Vite proxies `/api` locally.
4. FastAPI routers in `backend/app/api/` validate parameters and obtain a SQLAlchemy session through `get_db()`.
5. A domain agent loads records through `services/`, computes results with `utils/` and trained-model services, and applies recommendation rules.
6. JSON reaches React cards and Recharts visualizations. Investigations use a fetch-readable SSE stream, not Axios or EventSource.
7. FastAPI serves the Vite build for the application routes. API mistakes and missing bundle files return 404 instead of an HTML document disguised as JavaScript.

## Responsibility map

| Location | Responsibility |
|---|---|
| `backend/app/main.py` | App lifecycle, seeding, middleware, routers, SPA delivery, liveness/readiness |
| `core/config.py` | Environment settings, database URL normalization, provider and auth settings |
| `core/database.py` | Engine/session creation, SQLite WAL, table creation |
| `api/` | HTTP contracts and role checks |
| `models/` | SQLAlchemy persistence models and response/request schemas |
| `services/` | Database reads, CSV ingestion, durable handoffs, ML loading/inference |
| `utils/` | Analytics, feature engineering, drift checks, upload parsing, SSE encoding |
| `agents/` | Domain analysis and recommendations |
| `core/*_tools.py` | Callable operations exposed to investigation providers |
| `core/intelligence_engine.py` | Briefings, investigations, combined toolset, memory integration |
| `core/negotiation.py` | Detect a cost/maintenance conflict and generate three positions |
| `services/ai_providers/` | Mock, Groq, Gemini, and tool-schema adapters |
| `data/build_*_dataset.py` | Dataset preparation and provenance |
| `ml_models/*/train_*.py` | Offline training/evaluation; not run on each HTTP request |

## Three different kinds of intelligence

**Rules:** Thresholds and formulas written in Python. Energy recommendations examine off-hours load, HVAC share, trends, lighting, anomalies, and correlations. These are explainable heuristics; their savings estimates are not measured savings guarantees.

**Machine learning:** Saved estimators infer from engineered inputs. They do not understand facility operations semantically. Training and inference must use the same feature order, preprocessing, and model-compatible dependencies.

**LLM orchestration:** Groq can choose among schema-described tools, execute calls, see results, and continue until it answers or reaches an iteration cap. Gemini uses its provider integration. A briefing is a single generation call over existing analytics; it is not itself an agentic workflow.

**Mock mode:** `MockProvider` runs conditional Python branches and real tools. Tool effects are real, but the choice of tool is scripted. Never describe mock mode as autonomous LLM reasoning. `AIProvider`’s default stream replays completed results; Groq overrides it for events during execution. Streaming-compatible does not necessarily mean model-token streaming.

**Groq reliability:** Tool events arrive during execution; the completed summary is delivered once, without a second generation request. SDK retries are disabled; a 429 with a `retry-after` of at most ten seconds gets one request-only retry. Model fallback applies only to unavailable/decommissioned models before tool execution. A failed investigation never automatically replays mock tools, since a previous tool may already have committed an action. The free account's token quota can still interrupt a run; the UI reports that limitation.

## Domain details and current saved metrics

### Energy

- Source pipeline combines rescaled PJM load, weather, and occupancy data. A shared demo timeline and rescaling mean it is not a live building sensor feed.
- Inputs include time/calendar cycles, temperature, occupancy, current load, rolling means/standard deviations, momentum, daily/weekly lags, and submeter loads.
- Separate horizons use 15-minute steps: 1h = 4, 6h = 24, 24h = 96.
- Saved 1h winner: random-forest/gradient-boosting ensemble; MAE **4.06 kWh**, R² **0.9925**, **69.2%** improvement over the best naive baseline.
- Saved 6h winner: histogram gradient boosting; MAE **18.94 kWh**, R² **0.8698**, improvement **73.0%**.
- Saved 24h winner: histogram gradient boosting; MAE **27.81 kWh**, R² **0.743**, improvement **11.3%**. It remains a low-confidence horizon under the application's improvement thresholds.
- Forecasting requires at least 17 readings. Longer history improves lag availability. Inspect the training split before claiming absence of all leakage: time-ordered evaluation helps but is not a general proof.

### Maintenance

- NASA C-MAPSS FD001 engine trajectories are mapped onto fictional facility assets. Engine cycles are the native target unit. Displaying a maintenance date by adding cycles as days is a demo assumption, not a validated equipment-calendar forecast.
- Sensor features include rolling statistics, exponentially weighted features, changes, and ratios. Missing sensor inputs are imputed and disclosed.
- The lightweight runtime uses the saved tree ensemble: held-out MAE **12.31 cycles**, R² **0.825**, versus naive MAE **34.83**.
- Optional LSTM: 40-step sequences, LSTM(64) → LSTM(32) → dense layers; saved MAE **10.44 cycles**, R² **0.871**. This model requires the optional TensorFlow runtime.
- Health score maps clipped RUL to 0–100 with a 125-cycle clip; Excellent ≥75, Good ≥50, Warning ≥25, otherwise Critical.
- The nominal 80% quantile band has **74% empirical coverage** in the current artifact. Do not repeat the older README’s 80% empirical-coverage claim.
- Fleet inference batches model calls. Tool summaries should reuse the dashboard analysis rather than run an additional query per asset.

### Occupancy

- Primary binary classifier: logistic regression on UCI temperature, humidity, light, CO₂, and humidity ratio. Saved accuracy **98.34%**, F1 **0.9659**, majority baseline accuracy **75.67%**.
- Eight demo zones use projected utilization profiles. They are not eight independently instrumented real offices.
- Live classification of uploaded zone data requires environmental sensor columns; headcount alone is insufficient for that classifier.
- The separate one-hour utilization forecaster uses recent zone history and metadata. Saved MAE **7.75 percentage points**, improvement **24.3%** over the best naive baseline.
- Optional CNN: 10-reading windows, two Conv1D blocks, saved accuracy **98.52%**, F1 **0.9694**. It is disabled on the lightweight deployment. Its early-stopping metrics say the held-out data was used for validation selection: this is not an untouched final test set. A further independent split is needed for an unbiased final score.

### Security

- Access logs are synthetic with injected anomaly labels. The detector uses engineered access features, not the ground-truth label columns.
- Isolation Forest: saved precision **0.7141**, recall **0.7379**, F1 **0.7258**. These describe synthetic-pattern detection, not real-world incident performance.
- LOF is a comparison model; its `novelty=False` configuration cannot directly score arbitrary new observations without refitting.
- The supervised random-forest reference is evaluated with labels; it is not the live detector.
- A statistically unusual event is a lead for review, not proof of an intrusion.

### Cost

- Real BBMP tender records are combined with disclosed derived operating-cost records. Tender offices are not necessarily winning contractors. Dates are remapped for the demonstration.
- Isolation Forest flags 25 of 309 records (**8.1%**); agreement with LOF is **92.2%**. Agreement is not accuracy; there are no verified invoice-fraud labels.
- Random Forest forecasts a **forward three-week rolling average**, not a raw next-week invoice total. Saved MAE **₹1,190,776.29**, improvement **20.7%** over the selected naive forecast, but R² is **−0.145**. Be ready to explain how beating one naive baseline can coexist with negative R²: they compare against different reference predictions.
- Budgets are assumption-based. Derived cost records must not be misrepresented as measured invoices or injected into unrelated domain tables.

## Database and handoffs

| Domain | Main entities | Relationship |
|---|---|---|
| Auth | User | Unique username, bcrypt hash, admin/technician role |
| Energy | EnergyReading | Building/sensor/timestamp and energy/environment values |
| Maintenance | Asset, AssetReading, MaintenanceEvent | Readings and work orders refer to asset IDs |
| Occupancy | Zone, ZoneReading | Zone metadata and time-series readings |
| Security | AccessPoint, AccessEvent, SecurityAlert | Door events and cross-domain alerts |
| Cost | CostVendor, CostRecord, CostBudget, CostAlert | Records, category budgets, review flags |
| Memory | AgentMemory | Building/domain-scoped summaries, findings, provider, tool count |

Many relationships use string identifiers rather than database-enforced foreign keys. `building_id` is repeated on root entities; there is no normalized Building entity. This is a single-tenant demonstration, not a mature multitenant permissions system. Do not claim tenant isolation from the building selector alone.

Energy’s maintenance flag calls the same work-order persistence service used by Maintenance. Occupancy’s restricted-zone tool calls the Security alert service. The `source` field records the origin. This is synchronous application-level coordination, not a message broker or independently deployed agent network.

Memory stores recent summaries in SQL, not a vector database. Prompts include a bounded recap and ask tools to reverify current facts. Memory supports continuity, not guaranteed correctness or learning of new model weights.

Negotiation first checks the Repairs & Maintenance budget and risky assets. If a conflict exists, Cost and Maintenance each state a position and a mediator receives both plus the underlying data. The output is advice; it does not transfer funds, repair machines, or optimize a validated mathematical objective.

## Authentication and security discussion

Passwords are bcrypt-hashed. JWTs contain subject and expiry and use a configured signing algorithm/key. API dependencies check the user still exists and enforce roles on protected actions. Signup creates a technician, never an admin. Tokens are stored in localStorage: simple for a demo, but exposed to successful same-origin XSS; an HttpOnly-cookie design would be a sensible production improvement.

Read-side endpoints intentionally expose the shared demo dataset. Dataset ingestion, uploads, investigations, negotiation, and manual record changes require an admin or technician token. Public signup creates technicians, so this is still a collaborative demo rather than private multi-tenant software. Audit authorization endpoint-by-endpoint before using private facility data. Do not call the app production-secure merely because it has a login form. Additional production work includes rate limits, tenant boundaries, migrations, backups, secret rotation, upload limits, audit logs, and comprehensive permission tests.

## Performance and resilience

- Route-level lazy loading avoids downloading every dashboard at login. Separate React, chart, motion and icon bundles improve caching; splitting bundles does not eliminate their runtime cost.
- Cached model objects avoid repeated deserialization. Domain/facility caches avoid repeating expensive analytics. TTL and mutation invalidation must be balanced: fast stale values can be operationally wrong.
- Batched fleet inference avoids per-asset estimator overhead. SQL bulk reads avoid an N+1 query pattern. Measure queries and latency before and after changing them.
- SQLite WAL improves reader/writer coexistence but still has one writer. PostgreSQL is the deployment option for durable concurrent access.
- `/health` reports liveness; `/ready` reports seed-data readiness. An open HTTP port does not prove the data is ready.
- Authentication distinguishes invalid credentials from a temporary outage. Stream cancellation prevents old requests from replacing newer state; browser cancellation does not roll back tool side effects already committed on the server.
- Free hosting can sleep and has resource limits. Optional inference is explicitly unavailable when disabled; no predictions are fabricated to fill the UI.

## Questions to practice

1. **Why FastAPI?** Typed validation, generated OpenAPI, dependency injection and streaming responses fit the Python analytics stack. CPU-heavy inference still needs bounded concurrency or job workers at higher load.
2. **Why React context?** Auth, selected building, theme and notifications are shared UI state. It is not a full server-state cache; request lifecycle management still matters.
3. **Why one origin?** Relative API URLs simplify deployment and remove cross-origin browser configuration from the normal path. CORS is not authorization.
4. **What makes this agentic?** Tool selection can be model-driven with a real provider and tool effects persist. Explain the explicit limitation of mock mode.
5. **What is SSE?** An HTTP response carrying event frames. Fetch lets this implementation send bearer headers and cancel reads. WebSockets would be useful for bidirectional traffic but are unnecessary for one-way investigation results.
6. **Why not use an LLM for the numbers?** Deterministic analytics and trained estimators are inspectable and testable; the LLM interprets structured outputs and chooses tools.
7. **How do you prevent leakage?** Use chronological holdouts for forecasting, group engines for maintenance tuning, keep preprocessors fitted on training data, and reserve a genuinely untouched final test split. Acknowledge the CNN validation-selection caveat.
8. **Why MAE and F1?** MAE preserves target units and is interpretable; F1 balances precision and recall under class imbalance. Neither replaces operational cost analysis.
9. **What is drift here?** A lightweight comparison to training feature distributions, not a comprehensive distribution-shift detector or proof predictions are invalid.
10. **How are failures tested?** Regression tests recreate wrong URL defaults, expired versus unavailable sessions, truncated streams, disabled inference, stale caches, and zero-score handling. Integration tests use a disposable database.
11. **What would you scale next?** Database indexes and query profiling, shared/versioned caches across workers, asynchronous jobs for long inference, durable task status, tenant authorization, and observability. Avoid adding distributed systems without measured need.
12. **What is your strongest debugging example?** A valid zero fleet-health score was treated as falsy and became 100. A regression test separated `0` from `None`, then the implementation was fixed. Another example is the 101-query fleet tool despite an available cached analysis.
13. **What is not implemented?** Real building-control integrations, autonomous physical actuation, verified cost savings, comprehensive production authorization, and guaranteed free hosting availability. Explain the prototype boundary honestly.

## Preparation sequence

Day 1: Trace login and one dashboard from React to SQL and back. Day 2: Run an investigation, inspect the tool trace and persisted alert/work-order source. Day 3: Review one model’s features, split, baseline, metric and failure cases. Day 4: Explain the schema and deployment; reproduce a regression test. Day 5: Practice a five-minute architecture explanation and answer the questions above without reading.
