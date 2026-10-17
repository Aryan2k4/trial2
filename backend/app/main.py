import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import BASE_DIR, settings
from app.core.database import init_db, SessionLocal
from app.api.routes import router as energy_router
from app.api.maintenance_routes import router as maintenance_router
from app.api.occupancy_routes import router as occupancy_router
from app.api.security_routes import router as security_router
from app.api.cost_routes import router as cost_router
from app.api.facility_routes import router as facility_router
from app.api.system_routes import router as system_router
from app.api.auth_routes import router as auth_router
from app.services import data_service, maintenance_service, occupancy_service, security_service, cost_service
from app.core.security import hash_password
from app.models.auth_models import User

logger = logging.getLogger(__name__)

# The production container copies Vite's build output here. Keeping the API
# and SPA in one FastAPI process gives the app one public URL and lets browser
# requests use the relative /api path (no cross-origin configuration needed).
FRONTEND_DIST = BASE_DIR / "frontend_dist"
# In local development Vite writes to frontend/dist, whereas the production
# image copies that same build into backend/frontend_dist.
if not FRONTEND_DIST.is_dir():
    FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        # Seed the single demo admin user on first boot only — if ANY user
        # already exists (including one with a different username someone
        # created by hand), this is skipped, so it never clobbers a
        # password someone has since changed.
        if db.query(User).count() == 0:
            db.add(User(username=settings.ADMIN_USERNAME, password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin"))
            db.commit()
            logger.warning(
                f"Seeded default admin user '{settings.ADMIN_USERNAME}' with the password from "
                f"ADMIN_PASSWORD in .env. Change ADMIN_PASSWORD (and JWT_SECRET_KEY) before this "
                f"is anything other than a local demo."
            )
    finally:
        db.close()

    # Each domain owns its transaction. A failed import must not suppress
    # the remaining domains, and liveness is distinct from data readiness.
    jobs = [
        ("energy", data_service.has_data, data_service.ingest_from_csv),
        ("maintenance", maintenance_service.has_data, maintenance_service.ingest_fleet),
        ("occupancy", occupancy_service.has_data, occupancy_service.ingest_zones),
        ("security", security_service.has_data, security_service.ingest_events),
        ("cost", cost_service.has_data, cost_service.ingest_records),
    ]
    app.state.data_status = {name: "loading" for name, _, _ in jobs}

    def _run_background_ingest():
        for name, has_data, ingest in jobs:
            with SessionLocal() as db:
                try:
                    if not has_data(db, "BLD-HQ-01"):
                        ingest(db)
                    app.state.data_status[name] = "ready"
                except Exception:
                    db.rollback()
                    app.state.data_status[name] = "failed"
                    logger.exception("Startup ingestion failed for %s", name)

    import asyncio
    ingest_task = asyncio.create_task(asyncio.to_thread(_run_background_ingest))

    # Pre-warm the maintenance ML models (Keras LSTM + sklearn trees) at
    # server boot, not on the first real dashboard request. Loading is
    # already cached after the first use (see health_service._load_model/
    # _load_lstm), but the FIRST call in the process also pays for a
    # one-time TensorFlow graph trace, which is exactly the "dashboard
    # takes forever to open" cost users actually feel. Paying it here
    # means it happens while the server is starting up (invisible to the
    # user) instead of while they're staring at a loading spinner.
    # TensorFlow's model runtime exceeds the memory available on small/free
    # hosting plans. Set ENABLE_TENSORFLOW=false there so the rest of the
    # dashboard remains available; TensorFlow-specific endpoints already
    # report that their live model is unavailable instead of failing startup.
    default_enable = "false" if os.getenv("RENDER") else "true"
    if os.getenv("ENABLE_TENSORFLOW", default_enable).lower() not in {"1", "true", "yes"}:
        logger.info("TensorFlow model pre-warm disabled by ENABLE_TENSORFLOW or RENDER platform.")
    else:
        try:
            import numpy as np
            import pandas as pd
            from app.services import health_service
            dummy_df = pd.DataFrame({
                "cycle": range(1, 6), "timestamp": [pd.Timestamp.now()] * 5,
                "temp_stage1_c": np.zeros(5), "temp_stage2_c": np.zeros(5), "temp_stage3_c": np.zeros(5),
                "pressure_kpa": np.zeros(5), "vibration_index": np.zeros(5), "flow_rate": np.zeros(5),
                "efficiency_ratio": np.zeros(5), "bleed_load": np.zeros(5),
            })
            health_service.predict_fleet_health([dummy_df])  # loads+caches both models AND triggers the one-time TF graph trace now, not on the first real request
            logger.info("Maintenance ML models pre-warmed at startup.")
        except Exception as e:
            logger.warning(f"Model pre-warm skipped (non-fatal): {e}")

    try:
        yield
    finally:
        await ingest_task


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


# This MUST be registered before CORSMiddleware is added below. Starlette's
# middleware stack wraps outer-to-inner in add-order-reversed, and
# CORSMiddleware only adds its headers to responses that flow back UP
# through it — an exception that escapes past it entirely (e.g. from
# @app.exception_handler(Exception), which sits on the ServerErrorMiddleware
# layer OUTSIDE CORSMiddleware) never gets CORS headers attached, and the
# browser reports it as a generic, misleading "Network Error" even though
# the backend process is alive and every other request is working. Catching
# the exception here — INSIDE CORSMiddleware — turns it into a normal
# Response that CORSMiddleware still gets to process normally, for ANY
# endpoint, not just the AI-provider ones.
@app.middleware("http")
async def catch_unhandled_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred. Please retry.", "path": str(request.url.path)},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(energy_router, prefix=settings.API_V1_PREFIX)
app.include_router(maintenance_router, prefix=settings.API_V1_PREFIX)
app.include_router(occupancy_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_router, prefix=settings.API_V1_PREFIX)
app.include_router(cost_router, prefix=settings.API_V1_PREFIX)
app.include_router(facility_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX)
    return {"service": settings.PROJECT_NAME, "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def readiness():
    domains = getattr(app.state, "data_status", {})
    ready = bool(domains) and all(value == "ready" for value in domains.values())
    status = "ready" if ready else ("degraded" if "failed" in domains.values() else "loading")
    return JSONResponse(status_code=200 if ready else 503, content={"status": status, "domains": domains})


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    """Serve Vite assets directly and fall back to the SPA for client routes."""
    if not FRONTEND_INDEX.is_file():
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    # API typos must remain normal API 404s rather than returning the SPA.
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    requested_file = (FRONTEND_DIST / full_path).resolve()
    try:
        requested_file.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    if requested_file.is_file():
        return FileResponse(requested_file)
    if full_path.startswith("assets/") or Path(full_path).suffix:
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return FileResponse(FRONTEND_INDEX)
