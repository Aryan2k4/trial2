# FacilityOps source map

Generated from Python AST and frontend source paths. See INTERVIEW_GUIDE.md for explanations. Router-relative paths are mounted under /api plus each router prefix.

## API routes

| Method | Router-relative path | Handler | Source |
|---|---|---|---|
| POST | `/login` | `login` | `backend/app/api/auth_routes.py:27` |
| GET | `/me` | `me` | `backend/app/api/auth_routes.py:40` |
| POST | `/register` | `register` | `backend/app/api/auth_routes.py:52` |
| GET | `/users` | `list_users` | `backend/app/api/auth_routes.py:95` |
| POST | `/users` | `create_user` | `backend/app/api/auth_routes.py:102` |
| DELETE | `/users/{user_id}` | `delete_user` | `backend/app/api/auth_routes.py:124` |
| POST | `/ingest` | `ingest` | `backend/app/api/cost_routes.py:25` |
| GET | `/building` | `building` | `backend/app/api/cost_routes.py:38` |
| GET | `/vendors` | `vendors` | `backend/app/api/cost_routes.py:62` |
| GET | `/budgets` | `budgets` | `backend/app/api/cost_routes.py:71` |
| GET | `/records` | `records` | `backend/app/api/cost_routes.py:79` |
| GET | `/alerts` | `alerts` | `backend/app/api/cost_routes.py:89` |
| GET | `/investigate` | `investigate` | `backend/app/api/cost_routes.py:94` |
| GET | `/investigate/stream` | `investigate_stream` | `backend/app/api/cost_routes.py:101` |
| POST | `/ingest/upload` | `ingest_upload` | `backend/app/api/cost_routes.py:119` |
| GET | `/records/recent` | `recent_records` | `backend/app/api/cost_routes.py:175` |
| POST | `/records` | `add_record` | `backend/app/api/cost_routes.py:188` |
| DELETE | `/records/{record_id}` | `delete_record` | `backend/app/api/cost_routes.py:206` |
| DELETE | `/records` | `clear_all_records` | `backend/app/api/cost_routes.py:217` |
| GET | `/buildings` | `list_buildings` | `backend/app/api/facility_routes.py:54` |
| GET | `/health` | `facility_health` | `backend/app/api/facility_routes.py:181` |
| GET | `/alerts` | `facility_alerts` | `backend/app/api/facility_routes.py:225` |
| GET | `/kpis` | `facility_kpis` | `backend/app/api/facility_routes.py:240` |
| GET | `/investigate` | `facility_investigate` | `backend/app/api/facility_routes.py:270` |
| GET | `/investigate/stream` | `facility_investigate_stream` | `backend/app/api/facility_routes.py:285` |
| GET | `/negotiate` | `facility_negotiate` | `backend/app/api/facility_routes.py:291` |
| GET | `/search` | `facility_search` | `backend/app/api/facility_routes.py:307` |
| POST | `/ingest` | `ingest` | `backend/app/api/maintenance_routes.py:24` |
| GET | `/fleet` | `fleet` | `backend/app/api/maintenance_routes.py:37` |
| GET | `/assets` | `assets` | `backend/app/api/maintenance_routes.py:71` |
| GET | `/assets/{asset_id}` | `asset_detail` | `backend/app/api/maintenance_routes.py:78` |
| GET | `/assets/{asset_id}/history` | `asset_history` | `backend/app/api/maintenance_routes.py:92` |
| GET | `/alerts` | `alerts` | `backend/app/api/maintenance_routes.py:102` |
| GET | `/model/scatter` | `model_scatter` | `backend/app/api/maintenance_routes.py:114` |
| GET | `/work-orders` | `work_orders` | `backend/app/api/maintenance_routes.py:126` |
| GET | `/investigate` | `investigate` | `backend/app/api/maintenance_routes.py:138` |
| GET | `/investigate/stream` | `investigate_stream` | `backend/app/api/maintenance_routes.py:146` |
| POST | `/ingest/upload` | `ingest_upload` | `backend/app/api/maintenance_routes.py:170` |
| GET | `/records/recent` | `recent_records` | `backend/app/api/maintenance_routes.py:246` |
| POST | `/records` | `add_record` | `backend/app/api/maintenance_routes.py:261` |
| DELETE | `/records/{record_id}` | `delete_record` | `backend/app/api/maintenance_routes.py:282` |
| DELETE | `/records` | `clear_all_records` | `backend/app/api/maintenance_routes.py:294` |
| POST | `/ingest` | `ingest` | `backend/app/api/occupancy_routes.py:25` |
| GET | `/building` | `building` | `backend/app/api/occupancy_routes.py:37` |
| GET | `/cnn/summary` | `cnn_summary` | `backend/app/api/occupancy_routes.py:57` |
| GET | `/zones` | `zones` | `backend/app/api/occupancy_routes.py:69` |
| GET | `/zones/{zone_id}` | `zone_detail` | `backend/app/api/occupancy_routes.py:76` |
| GET | `/zones/{zone_id}/history` | `zone_history` | `backend/app/api/occupancy_routes.py:89` |
| GET | `/zones/{zone_id}/forecast` | `zone_forecast` | `backend/app/api/occupancy_routes.py:98` |
| GET | `/zones/{zone_id}/classify` | `zone_classify` | `backend/app/api/occupancy_routes.py:118` |
| GET | `/alerts` | `alerts` | `backend/app/api/occupancy_routes.py:135` |
| GET | `/investigate` | `investigate` | `backend/app/api/occupancy_routes.py:141` |
| GET | `/investigate/stream` | `investigate_stream` | `backend/app/api/occupancy_routes.py:149` |
| GET | `/cnn/live-inference` | `cnn_live_inference` | `backend/app/api/occupancy_routes.py:156` |
| GET | `/cnn/live-inference/{zone_id}` | `cnn_live_inference_on_zone` | `backend/app/api/occupancy_routes.py:169` |
| POST | `/ingest/upload` | `ingest_upload` | `backend/app/api/occupancy_routes.py:202` |
| GET | `/records/recent` | `recent_records` | `backend/app/api/occupancy_routes.py:280` |
| POST | `/records` | `add_record` | `backend/app/api/occupancy_routes.py:293` |
| DELETE | `/records/{record_id}` | `delete_record` | `backend/app/api/occupancy_routes.py:312` |
| DELETE | `/records` | `clear_all_records` | `backend/app/api/occupancy_routes.py:323` |
| POST | `/ingest` | `ingest` | `backend/app/api/routes.py:31` |
| POST | `/ingest/upload` | `ingest_upload` | `backend/app/api/routes.py:44` |
| GET | `/consumption` | `consumption` | `backend/app/api/routes.py:79` |
| GET | `/analytics` | `analytics` | `backend/app/api/routes.py:85` |
| GET | `/recommendations` | `recommendations` | `backend/app/api/routes.py:92` |
| GET | `/dashboard` | `dashboard` | `backend/app/api/routes.py:98` |
| GET | `/readings` | `readings` | `backend/app/api/routes.py:120` |
| GET | `/forecast` | `forecast` | `backend/app/api/routes.py:137` |
| GET | `/forecast/scatter` | `forecast_scatter` | `backend/app/api/routes.py:165` |
| GET | `/forecast/model-comparison` | `forecast_model_comparison` | `backend/app/api/routes.py:180` |
| GET | `/briefing` | `briefing` | `backend/app/api/routes.py:190` |
| GET | `/investigate` | `investigate` | `backend/app/api/routes.py:212` |
| GET | `/investigate/stream` | `investigate_stream` | `backend/app/api/routes.py:233` |
| GET | `/records/recent` | `recent_records` | `backend/app/api/routes.py:262` |
| POST | `/records` | `add_record` | `backend/app/api/routes.py:277` |
| DELETE | `/records/{record_id}` | `delete_record` | `backend/app/api/routes.py:295` |
| DELETE | `/records` | `clear_all_records` | `backend/app/api/routes.py:306` |
| POST | `/ingest` | `ingest` | `backend/app/api/security_routes.py:25` |
| GET | `/building` | `building` | `backend/app/api/security_routes.py:37` |
| GET | `/access-points` | `access_points` | `backend/app/api/security_routes.py:59` |
| GET | `/events` | `events` | `backend/app/api/security_routes.py:68` |
| GET | `/alerts` | `alerts` | `backend/app/api/security_routes.py:77` |
| GET | `/investigate` | `investigate` | `backend/app/api/security_routes.py:84` |
| GET | `/investigate/stream` | `investigate_stream` | `backend/app/api/security_routes.py:91` |
| POST | `/ingest/upload` | `ingest_upload` | `backend/app/api/security_routes.py:116` |
| GET | `/records/recent` | `recent_records` | `backend/app/api/security_routes.py:172` |
| POST | `/records` | `add_record` | `backend/app/api/security_routes.py:186` |
| DELETE | `/records/{record_id}` | `delete_record` | `backend/app/api/security_routes.py:206` |
| DELETE | `/records` | `clear_all_records` | `backend/app/api/security_routes.py:217` |
| GET | `/ai-status` | `ai_status` | `backend/app/api/system_routes.py:20` |
| GET | `/` | `root` | `backend/app/main.py:165` |
| GET | `/health` | `health` | `backend/app/main.py:172` |
| GET | `/ready` | `readiness` | `backend/app/main.py:177` |
| GET | `/{full_path:path}` | `serve_frontend` | `backend/app/main.py:185` |

## Backend modules

### `backend/app/agents/cost_agent.py`

`CostAgent` (line 32)

### `backend/app/agents/energy_agent.py`

`EnergyAgent` (line 38)

### `backend/app/agents/maintenance_agent.py`

`_get_lock` (line 23), `clear_maintenance_agent_cache` (line 30), `MaintenanceAgent` (line 35)

### `backend/app/agents/occupancy_agent.py`

`OccupancyAgent` (line 33)

### `backend/app/agents/security_agent.py`

`SecurityAgent` (line 34)

### `backend/app/api/auth_routes.py`

`LoginRequest` (line 14), `LoginResponse` (line 19), `login` (line 27), `me` (line 40), `RegisterRequest` (line 46), `register` (line 52), `CreateUserRequest` (line 80), `UserOut` (line 86), `list_users` (line 95), `create_user` (line 102), `delete_user` (line 124)

### `backend/app/api/cost_routes.py`

`ingest` (line 25), `building` (line 38), `vendors` (line 62), `budgets` (line 71), `records` (line 79), `alerts` (line 89), `investigate` (line 94), `investigate_stream` (line 101), `ingest_upload` (line 119), `CostRecordIn` (line 166), `recent_records` (line 175), `add_record` (line 188), `delete_record` (line 206), `clear_all_records` (line 217)

### `backend/app/api/facility_routes.py`

`list_buildings` (line 54), `_safe_analyze` (line 74), `_energy_subscore` (line 89), `_maintenance_subscore` (line 97), `_occupancy_subscore` (line 104), `_security_subscore` (line 113), `_cost_subscore` (line 124), `_get_analysis_lock` (line 145), `_get_agent_analyses` (line 152), `facility_health` (line 181), `facility_alerts` (line 225), `facility_kpis` (line 240), `facility_investigate` (line 270), `facility_investigate_stream` (line 285), `facility_negotiate` (line 291), `facility_search` (line 307)

### `backend/app/api/maintenance_routes.py`

`ingest` (line 24), `fleet` (line 37), `assets` (line 71), `asset_detail` (line 78), `asset_history` (line 92), `alerts` (line 102), `model_scatter` (line 114), `work_orders` (line 126), `investigate` (line 138), `investigate_stream` (line 146), `ingest_upload` (line 170), `AssetReadingIn` (line 231), `recent_records` (line 246), `add_record` (line 261), `delete_record` (line 282), `clear_all_records` (line 294)

### `backend/app/api/occupancy_routes.py`

`ingest` (line 25), `building` (line 37), `cnn_summary` (line 57), `zones` (line 69), `zone_detail` (line 76), `zone_history` (line 89), `zone_forecast` (line 98), `zone_classify` (line 118), `alerts` (line 135), `investigate` (line 141), `investigate_stream` (line 149), `cnn_live_inference` (line 156), `cnn_live_inference_on_zone` (line 169), `ingest_upload` (line 202), `ZoneReadingIn` (line 272), `recent_records` (line 280), `add_record` (line 293), `delete_record` (line 312), `clear_all_records` (line 323)

### `backend/app/api/routes.py`

`ingest` (line 31), `ingest_upload` (line 44), `consumption` (line 79), `analytics` (line 85), `recommendations` (line 92), `dashboard` (line 98), `readings` (line 120), `forecast` (line 137), `forecast_scatter` (line 165), `forecast_model_comparison` (line 180), `briefing` (line 190), `investigate` (line 212), `investigate_stream` (line 233), `EnergyReadingIn` (line 249), `recent_records` (line 262), `add_record` (line 277), `delete_record` (line 295), `clear_all_records` (line 306)

### `backend/app/api/security_routes.py`

`ingest` (line 25), `building` (line 37), `access_points` (line 59), `events` (line 68), `alerts` (line 77), `investigate` (line 84), `investigate_stream` (line 91), `_to_bool` (line 109), `ingest_upload` (line 116), `AccessEventIn` (line 164), `recent_records` (line 172), `add_record` (line 186), `delete_record` (line 206), `clear_all_records` (line 217)

### `backend/app/api/system_routes.py`

`ai_status` (line 20)

### `backend/app/core/agent_tools.py`

`get_consumption_summary` (line 23), `get_submeter_breakdown` (line 38), `get_anomalies` (line 53), `get_temperature_correlation` (line 70), `get_occupancy_correlation` (line 87), `get_ml_forecast` (line 104), `flag_for_maintenance_review` (line 127)

### `backend/app/core/cache_revision.py`

`current_revision` (line 13), `advance_revision` (line 18)

### `backend/app/core/config.py`

`Settings` (line 19)

### `backend/app/core/cost_tools.py`

`get_spend_summary` (line 13), `get_budget_compliance` (line 29), `get_flagged_invoices` (line 47), `get_spend_forecast` (line 67), `get_vendor_concentration` (line 84), `create_cost_alert` (line 102)

### `backend/app/core/database.py`

`get_db` (line 34), `init_db` (line 42)

### `backend/app/core/intelligence_engine.py`

`_safe_generate` (line 41), `_safe_agentic_task` (line 65), `summarize_energy_analysis` (line 215), `_run_investigation` (line 240), `_run_investigation_stream` (line 286), `investigate_energy` (line 329), `investigate_energy_stream` (line 340), `investigate_maintenance` (line 345), `investigate_maintenance_stream` (line 356), `investigate_occupancy` (line 361), `investigate_occupancy_stream` (line 371), `investigate_security` (line 376), `investigate_security_stream` (line 387), `investigate_cost` (line 392), `investigate_cost_stream` (line 402), `investigate_facility` (line 407), `investigate_facility_stream` (line 429)

### `backend/app/core/maintenance_tools.py`

`get_fleet_summary` (line 14), `get_asset_health` (line 29), `get_at_risk_assets` (line 50), `create_work_order` (line 67)

### `backend/app/core/negotiation.py`

`_get_at_risk_assets` (line 64), `_get_category_compliance` (line 73), `detect_conflict` (line 85), `negotiate` (line 99)

### `backend/app/core/occupancy_tools.py`

`get_building_occupancy_summary` (line 10), `get_zone_status` (line 31), `get_overcrowded_zones` (line 50), `get_restricted_zone_status` (line 70), `flag_restricted_zone_for_security_review` (line 94)

### `backend/app/core/security.py`

`hash_password` (line 19), `verify_password` (line 23), `create_access_token` (line 32), `decode_access_token` (line 38), `get_current_user` (line 44), `require_role` (line 71)

### `backend/app/core/security_tools.py`

`get_security_summary` (line 10), `get_flagged_events` (line 30), `get_access_point_risk` (line 50), `create_security_alert` (line 68)

### `backend/app/main.py`

`lifespan` (line 37), `catch_unhandled_exceptions` (line 134), `root` (line 165), `health` (line 172), `readiness` (line 177), `serve_frontend` (line 185)

### `backend/app/models/agent_memory_models.py`

`AgentMemory` (line 5)

### `backend/app/models/auth_models.py`

`User` (line 5)

### `backend/app/models/cost_models.py`

`CostVendor` (line 5), `CostRecord` (line 20), `CostBudget` (line 39), `CostAlert` (line 52)

### `backend/app/models/energy_models.py`

`EnergyReading` (line 5)

### `backend/app/models/maintenance_models.py`

`Asset` (line 5), `AssetReading` (line 22), `MaintenanceEvent` (line 60)

### `backend/app/models/occupancy_models.py`

`Zone` (line 5), `ZoneReading` (line 19)

### `backend/app/models/schemas.py`

`EnergyReadingOut` (line 6), `IngestResponse` (line 18), `ConsumptionSummary` (line 25), `SubmeterBreakdown` (line 35), `AnomalyOut` (line 46), `Recommendation` (line 54), `DashboardSummary` (line 63)

### `backend/app/models/security_models.py`

`AccessPoint` (line 5), `AccessEvent` (line 17), `SecurityAlert` (line 45)

### `backend/app/services/agent_memory_service.py`

`save_memory` (line 24), `get_recent_memories` (line 48), `format_memory_context` (line 75), `extract_key_findings` (line 93)

### `backend/app/services/ai_providers/base.py`

`AIProvider` (line 11)

### `backend/app/services/ai_providers/factory.py`

`get_ai_provider` (line 19)

### `backend/app/services/ai_providers/gemini_provider.py`

`GeminiProvider` (line 31)

### `backend/app/services/ai_providers/groq_provider.py`

`GroqProvider` (line 16)

### `backend/app/services/ai_providers/mock_provider.py`

`MockProvider` (line 12)

### `backend/app/services/ai_providers/tool_schema.py`

`_parse_arg_descriptions` (line 16), `function_to_tool_schema` (line 39)

### `backend/app/services/cost_service.py`

`ingest_records` (line 28), `has_data` (line 83), `get_records_df` (line 88), `list_vendors` (line 104), `list_budgets` (line 108), `open_alert` (line 114), `list_alerts` (line 141)

### `backend/app/services/data_service.py`

`_read_any` (line 43), `_looks_like_our_schema` (line 51), `_normalize_external_df` (line 55), `_load_and_normalize` (line 93), `ingest_from_csv` (line 101), `get_readings_df` (line 132), `has_data` (line 164)

### `backend/app/services/forecast_service.py`

`get_prediction_scatter` (line 28), `_model_path` (line 45), `_load_model` (line 49), `is_model_available` (line 61), `get_horizon_confidence` (line 65), `get_model_comparison` (line 93), `get_data_drift` (line 115), `forecast` (line 134), `forecast_next_hour` (line 214)

### `backend/app/services/health_service.py`

`get_prediction_scatter` (line 34), `is_model_available` (line 56), `_get_metrics` (line 60), `_get_live_model_name` (line 72), `is_lstm_live` (line 81), `_load_lstm` (line 96), `_build_lstm_sequence` (line 108), `_load_model` (line 125), `get_data_drift` (line 136), `get_confidence` (line 156), `rul_to_health_score` (line 193), `health_score_to_status` (line 197), `_impute_missing_sensors` (line 204), `_build_features` (line 230), `predict_asset_health` (line 242), `predict_fleet_health` (line 255)

### `backend/app/services/maintenance_service.py`

`ingest_fleet` (line 32), `has_data` (line 84), `list_assets` (line 89), `get_asset` (line 93), `get_readings_df` (line 97), `get_all_readings_df` (line 123), `get_latest_readings_df` (line 157), `open_work_order` (line 173), `list_work_orders` (line 208), `pick_hvac_asset_for_energy_flag` (line 219)

### `backend/app/services/occupancy_cnn_service.py`

`_get_model` (line 30), `_get_activation_model` (line 40), `_get_live_data` (line 66), `is_available` (line 73), `run_live_inference` (line 77), `run_live_inference_on_zone` (line 148)

### `backend/app/services/occupancy_forecast_service.py`

`is_available` (line 27), `_load_model` (line 31), `get_confidence` (line 37), `get_data_drift` (line 55), `forecast_zone_utilization` (line 71)

### `backend/app/services/occupancy_ml_service.py`

`_load_model` (line 44), `classify_zone` (line 51)

### `backend/app/services/occupancy_service.py`

`ingest_zones` (line 20), `has_data` (line 64), `list_zones` (line 69), `get_zone` (line 73), `get_readings_df` (line 77), `get_all_zone_readings` (line 91), `get_latest_readings_df` (line 113)

### `backend/app/services/security_service.py`

`ingest_events` (line 26), `has_data` (line 69), `list_access_points` (line 74), `get_recent_events_df` (line 78), `get_first_visit_timestamps` (line 109), `open_alert` (line 129), `list_alerts` (line 163)

### `backend/app/utils/cost_analytics.py`

`is_model_available` (line 29), `_load` (line 33), `get_anomaly_model_confidence` (line 39), `get_anomaly_comparison_confidence` (line 45), `get_forecast_confidence` (line 51), `get_data_drift` (line 57), `_engineer_anomaly_features` (line 85), `score_records` (line 100), `top_flagged_records` (line 114), `forecast_trend` (line 127), `budget_compliance` (line 184), `vendor_concentration` (line 212), `spend_summary` (line 233), `category_breakdown` (line 245)

### `backend/app/utils/csv_upload.py`

`read_any` (line 16), `resolve_columns` (line 24), `save_upload_tmp` (line 46)

### `backend/app/utils/drift_detection.py`

`compute_drift` (line 23)

### `backend/app/utils/energy_analytics.py`

`consumption_summary` (line 12), `submeter_breakdown` (line 31), `trend_pct` (line 49), `detect_anomalies` (line 61), `off_hours_baseline_waste` (line 102), `temperature_correlation` (line 126), `occupancy_correlation` (line 150)

### `backend/app/utils/maintenance_analytics.py`

`score_asset` (line 12), `score_fleet` (line 31), `degradation_trend` (line 49), `fleet_summary` (line 64), `risk_ranking` (line 84)

### `backend/app/utils/occupancy_analytics.py`

`utilization_status` (line 26), `get_model_confidence` (line 39), `get_cnn_model_confidence` (line 56), `zone_status` (line 81), `building_summary` (line 116), `heatmap_data` (line 136), `overcrowding_alerts` (line 155), `generate_ai_insights` (line 159), `best_available_zone` (line 214)

### `backend/app/utils/rul_features.py`

`add_engineered_features` (line 58), `AveragingEnsemble` (line 111), `top_contributing_factors` (line 162)

### `backend/app/utils/security_analytics.py`

`_load_model` (line 27), `is_model_available` (line 34), `get_model_confidence` (line 38), `get_data_drift` (line 52), `get_comparison_model_confidence` (line 73), `get_supervised_reference_confidence` (line 92), `_engineer_features` (line 111), `score_events` (line 161), `building_security_summary` (line 180), `top_flagged_events` (line 196), `access_point_heatmap` (line 211), `access_point_activity` (line 240)

### `backend/app/utils/sse.py`

`_format_sse` (line 12), `sse_stream_response` (line 23)


## Frontend source files

- `frontend/src/App.jsx`
- `frontend/src/components/agent/AgentInvestigationPanel.jsx`
- `frontend/src/components/agent/AgentTraceViewer.jsx`
- `frontend/src/components/agent/traceFormatters.js`
- `frontend/src/components/auth/ProtectedRoute.jsx`
- `frontend/src/components/cards/BriefingCard.jsx`
- `frontend/src/components/cards/ForecastCard.jsx`
- `frontend/src/components/cards/HeroStatCard.jsx`
- `frontend/src/components/cards/KpiCard.jsx`
- `frontend/src/components/cards/RecommendationsList.jsx`
- `frontend/src/components/charts/BreakdownChart.jsx`
- `frontend/src/components/charts/ConsumptionChart.jsx`
- `frontend/src/components/charts/ModelReliabilityChart.jsx`
- `frontend/src/components/cost/BudgetComplianceList.jsx`
- `frontend/src/components/cost/CategorySpendChart.jsx`
- `frontend/src/components/cost/CostAlertsList.jsx`
- `frontend/src/components/cost/CostKpiRow.jsx`
- `frontend/src/components/cost/CostModelComparison.jsx`
- `frontend/src/components/cost/FlaggedInvoicesList.jsx`
- `frontend/src/components/cost/SpendTrendChart.jsx`
- `frontend/src/components/cost/VendorConcentrationCard.jsx`
- `frontend/src/components/energy/ForecastModelComparison.jsx`
- `frontend/src/components/energy/SectionTabs.jsx`
- `frontend/src/components/energy/SystemAssetGrid.jsx`
- `frontend/src/components/ErrorBoundary.jsx`
- `frontend/src/components/executive/FacilityHealthGauge.jsx`
- `frontend/src/components/executive/NegotiationPanel.jsx`
- `frontend/src/components/executive/UnifiedAlertFeed.jsx`
- `frontend/src/components/maintenance/AssetDetailPanel.jsx`
- `frontend/src/components/maintenance/AssetTable.jsx`
- `frontend/src/components/maintenance/Card.jsx`
- `frontend/src/components/maintenance/CriticalAssetsSpotlight.jsx`
- `frontend/src/components/maintenance/FleetHealthRadar.jsx`
- `frontend/src/components/maintenance/FleetKpiRow.jsx`
- `frontend/src/components/maintenance/MaintenanceAlertsList.jsx`
- `frontend/src/components/maintenance/SectionHeader.jsx`
- `frontend/src/components/maintenance/WorkOrdersPanel.jsx`
- `frontend/src/components/occupancy/AiInsightsPanel.jsx`
- `frontend/src/components/occupancy/CnnModelPanel.jsx`
- `frontend/src/components/occupancy/OccupancyAlertsList.jsx`
- `frontend/src/components/occupancy/OccupancyKpiRow.jsx`
- `frontend/src/components/occupancy/ZoneDetailPanel.jsx`
- `frontend/src/components/occupancy/ZoneHeatmap.jsx`
- `frontend/src/components/occupancy/ZoneTable.jsx`
- `frontend/src/components/security/AccessPointRiskGrid.jsx`
- `frontend/src/components/security/FlaggedEventsList.jsx`
- `frontend/src/components/security/RiskHeatmap.jsx`
- `frontend/src/components/security/SecurityAlertsList.jsx`
- `frontend/src/components/security/SecurityKpiRow.jsx`
- `frontend/src/components/security/SecurityModelComparison.jsx`
- `frontend/src/components/shared/DataManagerModal.jsx`
- `frontend/src/components/shared/DatasetUploadPanel.jsx`
- `frontend/src/components/shell/AppShell.jsx`
- `frontend/src/components/shell/BuildingSwitcher.jsx`
- `frontend/src/components/shell/CommandPalette.jsx`
- `frontend/src/components/shell/NotificationBell.jsx`
- `frontend/src/components/ui/AnimatedNumber.jsx`
- `frontend/src/components/ui/ConnectionError.jsx`
- `frontend/src/components/ui/DashboardHeader.jsx`
- `frontend/src/components/ui/DashboardSkeleton.jsx`
- `frontend/src/components/ui/DataDriftBanner.jsx`
- `frontend/src/components/ui/LiveIndicator.jsx`
- `frontend/src/components/ui/ThemeToggle.jsx`
- `frontend/src/components/ui/Toast.jsx`
- `frontend/src/context/AuthContext.jsx`
- `frontend/src/context/BuildingContext.jsx`
- `frontend/src/context/ThemeContext.jsx`
- `frontend/src/context/ToastContext.jsx`
- `frontend/src/hooks/useAgentStream.js`
- `frontend/src/index.css`
- `frontend/src/main.jsx`
- `frontend/src/pages/cost/CostDashboardPage.jsx`
- `frontend/src/pages/energy/EnergyDashboardPage.jsx`
- `frontend/src/pages/executive/ExecutiveDashboardPage.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/maintenance/MaintenanceDashboardPage.jsx`
- `frontend/src/pages/occupancy/OccupancyDashboardPage.jsx`
- `frontend/src/pages/security/SecurityDashboardPage.jsx`
- `frontend/src/pages/SignupPage.jsx`
- `frontend/src/services/apiConfig.js`
- `frontend/src/services/costService.js`
- `frontend/src/services/energyService.js`
- `frontend/src/services/maintenanceService.js`
- `frontend/src/services/occupancyService.js`
- `frontend/src/services/securityService.js`
- `frontend/src/test/AllProviders.jsx`
- `frontend/src/test/setup.js`
