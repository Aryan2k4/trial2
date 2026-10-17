from fastapi.testclient import TestClient
from app.main import app
from app.api.facility_routes import _maintenance_subscore
from app.services import occupancy_cnn_service
import pytest


@pytest.mark.parametrize('domain', ['energy', 'maintenance', 'occupancy', 'security', 'cost'])
def test_anonymous_users_cannot_replace_datasets(domain):
    assert TestClient(app).post(f'/api/{domain}/ingest').status_code == 401


@pytest.mark.parametrize('domain', ['energy', 'maintenance', 'occupancy', 'security', 'cost', 'facility'])
def test_anonymous_users_cannot_start_mutating_investigations(domain):
    assert TestClient(app).get(f'/api/{domain}/investigate/stream').status_code == 401


def test_cost_records_with_missing_optional_fields_are_json_serializable():
    from app.core.security import create_access_token
    client = TestClient(app, headers={'Authorization': f'Bearer {create_access_token("admin")}'})
    created = client.post('/api/cost/records', json={'vendor_name': 'Optional fields regression', 'category': 'Repairs & Maintenance', 'amount_inr': 1})
    assert created.status_code == 200
    try:
        response = client.get('/api/cost/records', params={'limit': 1000})
        assert response.status_code == 200
        assert any(row['vendor_name'] == 'Optional fields regression' for row in response.json()['records'])
    finally:
        client.delete(f"/api/cost/records/{created.json()['id']}")


def test_zero_health_is_not_reported_as_perfect():
    assert _maintenance_subscore({"fleet": {"avg_health_score": 0}}) == 0


def test_disabled_cnn_never_loads_tensorflow(monkeypatch):
    monkeypatch.setenv("ENABLE_TENSORFLOW", "false")
    def forbidden():
        raise AssertionError("Disabled runtime attempted to load TensorFlow")
    monkeypatch.setattr(occupancy_cnn_service, "_get_activation_model", forbidden)
    result = occupancy_cnn_service.run_live_inference()
    assert result["available"] is False
    assert result["reason"] == "tensorflow_disabled"


def test_missing_asset_is_not_html():
    with TestClient(app) as client:
        response = client.get("/assets/missing-bundle.js")
        assert response.status_code == 404
        assert "text/html" not in response.headers.get("content-type", "")


def test_readiness_does_not_claim_success_during_ingestion():
    app.state.data_status = {"energy": "loading", "cost": "ready"}
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "loading"
    app.state.data_status = {"energy": "ready", "cost": "ready"}
    assert client.get("/ready").status_code == 200


def test_fleet_tool_reuses_dashboard_analysis_without_per_asset_queries():
    from sqlalchemy import event
    from app.core.database import engine, SessionLocal
    from app.agents.maintenance_agent import MaintenanceAgent, clear_maintenance_agent_cache
    from app.core.maintenance_tools import get_fleet_summary
    clear_maintenance_agent_cache()
    with SessionLocal() as db:
        expected = MaintenanceAgent(db).analyze()["fleet"]
    queries = []
    def record(connection, cursor, statement, parameters, context, many):
        queries.append(statement)
    event.listen(engine, "before_cursor_execute", record)
    try:
        assert get_fleet_summary() == expected
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert len(queries) <= 2, "Fleet tool must not reload every asset's history"


def test_energy_analysis_updates_immediately_after_committed_data_change():
    from datetime import datetime
    from app.core.database import SessionLocal
    from app.models.energy_models import EnergyReading
    from app.agents.energy_agent import EnergyAgent
    with SessionLocal() as db:
        row = EnergyReading(building_id="CACHE-TEST", sensor_id="test", timestamp=datetime(2026, 1, 1, 12), total_kwh=10, hvac_kwh=5, lighting_kwh=2, plug_load_kwh=2, other_kwh=1)
        db.add(row)
        db.commit()
        first = EnergyAgent(db, "CACHE-TEST").analyze()["consumption"]["total_kwh"]
        row.total_kwh = 25
        db.commit()
        second = EnergyAgent(db, "CACHE-TEST").analyze()["consumption"]["total_kwh"]
        assert first == 10
        assert second == 25


def test_default_security_window_excludes_other_buildings():
    from datetime import datetime
    from app.core.database import SessionLocal
    from app.models.security_models import AccessPoint, AccessEvent
    from app.services.security_service import get_recent_events_df
    with SessionLocal() as db:
        db.add(AccessPoint(building_id="OTHER", access_point_id="OTHER-DOOR", name="Other door", risk_level="low"))
        db.add(AccessEvent(event_id="OTHER-EVENT", access_point_id="OTHER-DOOR", employee_id="OTHER-EMP", timestamp=datetime(2099, 1, 1), access_granted=True, risk_level="low"))
        db.commit()
        frame = get_recent_events_df(db)
        assert "OTHER-DOOR" not in frame["access_point_id"].tolist()
